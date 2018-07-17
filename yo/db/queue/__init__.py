# -*- coding: utf-8 -*-
import asyncio
import sqlalchemy as sa
import structlog
from concurrent.futures import ThreadPoolExecutor

from typing import TypeVar
from asyncpg.pool import Pool
from asyncpg.connection import Connection
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


async def _worker(database_url:str,
                  num_workers:int=10,
                  q_visibility_timeout:int=5,
                  worker_func=None,
                  worker_func_kwargs=None) -> None:

    workers = []
    for i in range(num_workers):
      workers.append(worker_factory(database_url,q_visibility_timeout,worker_func, worker_func_kwargs ))


class QItem:
    __slots__ = ('conn', 'tx','subtx','qitem','logger','timers')

    def __init__(self, conn, logger):
        self.conn = conn
        self.tx = None
        self.subtx = None
        self.qitem = None
        self.logger = logger
        self.timers = None

    async def __aenter__(self):
        # start main transation
        self.tx = self.conn.transaction()
        await self.tx.start()
        qitem = await self.conn.fetchrow(POP_Q_STMT)
        if not qitem: # item might have been removed before we got it
            self.logger.debug('no qitem')
            return
        self.qitem = qitem
        self.logger.debug('passing qitem', qid=self.qitem['qid'])
        return self.qitem

    async def __aexit__(self, extype, ex, tb):
        if extype is not None:
            await self.tx.rollback()
            self.logger.debug('returning qitem to q', qid=self.qitem['qid'])
        else:
            await self.tx.commit()
            self.logger.debug('deleted qitem from q', qid=self.qitem['qid'])

async def worker_factory(database_url,q_visibility_timeout,worker_func, worker_func_kwargs ):
    async def q_worker(database_url,q_visibility_timeout,worker_func, worker_func_kwargs):
        idle_in_transaction_session_timeout = q_visibility_timeout * 1000
        conn = await yo.db.create_asyncpg_conn(database_url, idle_in_transaction_session_timeout=idle_in_transaction_session_timeout)
        local_logger = logger.bind()

        while True:
            async with QItem(conn, local_logger) as qitem:
                if not qitem:
                    local_logger.debug('no qitem available')
                    await asyncio.sleep(0)  # yield to others
                local_logger.debug('qitem marked invisible', qitem=qitem['qid'])
                await worker_func(qitem, local_logger, worker_func_kwargs)
