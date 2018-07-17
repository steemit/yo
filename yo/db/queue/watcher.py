# -*- coding: utf-8 -*-
import asyncio
import dateutil
import dateutil.parser
import sqlalchemy as sa
import structlog
import toolz
from functools import partial
from concurrent.futures import ThreadPoolExecutor

from typing import TypeVar
from asyncpg.pool import Pool
from asyncpg.connection import Connection
from asyncio.queues import Queue
from time import perf_counter

from sqlalchemy.dialects.postgresql import JSONB
import asyncpg
import yo.db

from yo.db import metadata
from yo.schema import TransportType
from yo.json import loads

logger = structlog.getLogger(__name__, source='YoDB')

PoolOrConn = TypeVar('PoolOrConn', Pool, Connection)
QItemId = int
NotificationId = int

EXECUTOR = ThreadPoolExecutor()

PUSH_Q_STMT = '''
INSERT INTO queue(data,transport) VALUES($1,$2) RETURNING qid
'''

POP_Q_STMT = '''
DELETE FROM queue
WHERE qid = (
  SELECT qid
  FROM queue
  ORDER BY qid
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
RETURNING qid, data;
'''

POP_Q_BY_ID_STMT = '''
DELETE FROM queue
WHERE qid = (
  SELECT qid
  FROM queue
  WHERE qid=$1
  FOR UPDATE SKIP LOCKED
)
RETURNING qid, data;
'''

Q_ITER_STMT = '''
  SELECT qid
  FROM queue
  ORDER BY qid DESC
  LIMIT 1000
'''

Q_ITER__WITH_OFFSET_STMT = '''
  SELECT qid
  FROM queue
  WHERE qid > $1
  ORDER BY qid DESC
  LIMIT 1000
'''

Q_SIZE_STMT = '''
SELECT COUNT(*) FROM queue;
'''

NEWEST_QID_STMT = '''
SELECT qid
FROM queue
ORDER BY qid DESC
LIMIT 1
'''

WATCH_Q_TABLE_STMT = '''
SELECT watch_queue_table($1, $2);
'''

UNWATCH_Q_TABLE_STMT = '''
SELECT unwatch_queue_table($1, $2);
'''

NOTIFY_STMT = '''SELECT pg_notify($1, $2)'''

SET_QUEUE_TIMEOUT_MS_STMT = '''SET idle_in_transaction_session_timeout=$1;'''


queue = sa.Table(
    'queue',
    metadata,
    sa.Column('qid', sa.BigInteger(), primary_key=True),
    sa.Column('data', JSONB(), index=False, nullable=False),
    sa.Column('transport', sa.Integer(), index=True),
    sa.Column('timestamp', sa.TIMESTAMP, default=sa.func.now, index=True)
)

async def put(conn:PoolOrConn, data:dict, transport_type:TransportType) -> int:
    logger.debug(f'enqueing {data["nid"]} for transport type {transport_type.name}')
    return await conn.fetchval(PUSH_Q_STMT, data, transport_type.value)

async def put_many(conn:PoolOrConn, q_items:list):
    await conn.executemany(PUSH_Q_STMT, q_items)

async def get(conn:PoolOrConn) -> asyncpg.Record:
    return await conn.fetchrow(POP_Q_STMT)

async def size(conn:PoolOrConn) -> int:
    return await conn.fetchval(Q_SIZE_STMT)

async def watch(conn:Connection, table_name:str, channel:str) -> None:
    await conn.execute(WATCH_Q_TABLE_STMT, table_name, channel)

async def unwatch(conn:Connection, table_name:str, channel:str) -> None:
    await conn.execute(UNWATCH_Q_TABLE_STMT, table_name, channel)

async def newest_qid(conn:Connection) -> int:
    return await conn.fetchval(NEWEST_QID_STMT)


class QItem:
    __slots__ = ('conn', 'tx', 'conn','qitem',)

    def __init__(self, conn):
        self.conn = conn
        self.tx = None
        self.qitem = None

    async def __aenter__(self):
        while await size(self.conn) <= 0:
            await asyncio.sleep(0)
        self.tx = self.conn.transaction()
        await self.tx.start()
        while True:
            row = await self.conn.fetchrow(POP_Q_STMT)
            if not row: # item might have been removed before we got it
                await asyncio.sleep(0)
                continue
            logger.debug('q query returned row', item=row)
            break
        self.qitem = row
        logger.debug('passing q item to worker', itemid=self.qitem['id'])
        return self.qitem['data']

    async def __aexit__(self, extype, ex, tb):
        if extype is not None:
            await self.tx.rollback()
            logger.debug('rolling back, leaving item on q', itemid=self.qitem['id'])
        else:
            await self.tx.commit()
            logger.debug('committing, item deleted from q', itemid=self.qitem['id'])

class QueueStorage:
    '''A mixin class to preserve compatability with asyncio.Queue which
    calls len(self._queue)
    '''
    def __init__(self, loop, pool):
        self.loop = loop
        self.pool = pool


    def __len__(self) -> int:
        return self.loop.run_until_complete(size(self.pool))

class WorkQueue(Queue):

    def __init__(self, loop=None, pool=None, transport_type:TransportType=None):
        self.pool = pool
        self.transport_type = transport_type
        super().__init__(loop=loop)

    def _init(self, maxsize):
        self._queue = QueueStorage(self._loop, self.pool)

    def _get(self):
        return self._loop.run_until_complete(get(self.pool))

    def _put(self, item):
        return self._loop.run_until_complete(
            put(self.pool, data=item, transport_type=self.transport_type))


async def worker_function(payload,worker_conn_pool=None, source=None, **kwargs):
    if isinstance(payload, (str, bytes)):
        payload = loads(payload)
    qid = payload['qid']
    local_logger = logger.bind(qid=qid, source=source)
    local_logger.debug('worker_function', payload=payload)
    async with worker_conn_pool.acquire() as conn:
        tx = conn.transaction()
        try:
            await tx.start()
            row = await conn.fetchrow(POP_Q_BY_ID_STMT, qid)
            if not row:
                local_logger.debug('no free item in q')
                await tx.rollback()
                return
            local_logger.debug('worker_function received qitem', item=row)
            await asyncio.sleep(1)
        except Exception as e:
            await tx.rollback()
            local_logger.exception('worker_function error')
        else:
            await tx.commit()
            local_logger.debug('worker_function success')


def queue_callback(conn, pid, channel, payload, worker_func=None, worker_conn_pool=None, **kwargs):
    #logger.debug('NOTIFY', conn=conn, pid=pid, channel=channel, payload=payload,payload_type=type(payload))
    asyncio.ensure_future(worker_func(payload, worker_conn_pool=worker_conn_pool, source='notify',**kwargs))


async def queue_watcher(database_url,
                        channel='queue_changefeed',
                        callback_func=queue_callback,
                        worker_func=None,
                        worker_func_kwargs=None):
    worker_func_kwargs = worker_func_kwargs or dict()
    worker_conn_pool = await yo.db.create_asyncpg_pool(database_url)
    conn = await yo.db.create_asyncpg_conn(database_url)
    starting_qid = await newest_qid(conn)


    callback_func = partial(callback_func,
                            worker_func=worker_func,
                            worker_conn_pool=worker_conn_pool,
                            **worker_func_kwargs)
    await conn.add_listener(channel, callback_func)

    while True:
        logger.error('restart watcher loop')
        qsize = await size(conn)
        logger.error('restart watcher loop', qsize=qsize, tasks=len(asyncio.Task.all_tasks()))
        async with worker_conn_pool.acquire() as conn2:
            payloads = await conn2.fetch(Q_ITER_STMT)
            logger.debug('backlog qitem mark_sent to worker')
            args = [(channel,f'{{"qid":{payload["qid"]},"source":"backlog"}}') for payload in payloads]
            await conn2.executemany(NOTIFY_STMT,args)



