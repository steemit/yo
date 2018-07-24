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



async def watch(conn:Connection, table_name:str, channel:str) -> None:
    await conn.execute(WATCH_Q_TABLE_STMT, table_name, channel)

async def unwatch(conn:Connection, table_name:str, channel:str) -> None:
    await conn.execute(UNWATCH_Q_TABLE_STMT, table_name, channel)

async def newest_qid(conn:Connection) -> int:
    return await conn.fetchval(NEWEST_QID_STMT)



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
    logger.debug('NOTIFY', conn=conn, pid=pid, channel=channel, payload=payload,payload_type=type(payload))
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



