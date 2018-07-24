# -*- coding: utf-8 -*-
import asyncio
import sqlalchemy as sa
import structlog
from concurrent.futures import ThreadPoolExecutor

from typing import TypeVar
from typing import Awaitable
from asyncpg.pool import Pool
from asyncpg.connection import Connection
from time import perf_counter
from functools import partial

from sqlalchemy.dialects.postgresql import JSONB
import asyncpg
import yo.db

from yo.db import metadata
from yo.schema import TransportType
from yo.json import loads
from yo.db.actions import store
from yo.db.actions import mark_failed
from yo.db.actions import mark_rate_limited
from yo.db.actions import mark_sent
from yo.db.actions import RateLimitException
from yo.db.actions import PermanentFailException
from yo.db.actions import SendError


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
RETURNING qid, data, transport;
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
    __slots__ = ('conn', 'tx','qitem','logger','timers',
                 'qid','nid','transport','username')

    def __init__(self, conn, logger, timers=None):
        self.conn = conn
        self.tx = None
        self.qitem = None
        self.logger = logger
        self.timers = timers or dict()
        self.qid = None
        self.nid = None
        self.transport = None
        self.username = None

    async def __aenter__(self):
        # start main transation
        self.tx = self.conn.transaction()
        await self.tx.start()
        self.timers['transaction.start'] = perf_counter()
        qitem = await self.conn.fetchrow(POP_Q_STMT)
        self.timers['qitem.returned'] = perf_counter()
        if not qitem: # item might have been removed/processed before we got it
            self.logger.debug('no qitem', qitem=qitem)
            return
        self.logger.debug('qitem', qitem=qitem)

        self.qid = qitem['qid']
        self.transport = qitem['transport']
        self.nid = qitem['data']['nid']
        self.username = qitem['data']['to_username']
        self.qitem = qitem

        self.logger = self.logger.bind(qid=self.qid,
                                       nid=self.nid,
                                       transport=self.transport,
                                       username=self.username)
        return self.qitem

    async def __aexit__(self, extype, ex, tb):
        self.timers['qitem.aexit.begin'] = perf_counter()
        if extype is not None:
            self.timers['qitem.aexit.rollback'] = perf_counter()
            await self.tx.rollback()
            self.timers['qitem.aexit.rolled_back'] = perf_counter()
            if isinstance(ex, RateLimitException):
                self.timers['qitem.aexit.mark_rate_limited.start'] = perf_counter()
                await mark_rate_limited(self.conn,self.nid, self.username, self.transport)
                self.timers[
                    'qitem.aexit.mark_rate_limited.complete'] = perf_counter()
            elif isinstance(ex, (PermanentFailException, SendError)):
                self.timers[
                    'qitem.aexit.mark_failed.start'] = perf_counter()
                #await mark_failed(self.conn, self.nid, self.username,
                #                        self.transport)
                self.timers[
                    'qitem.aexit.mark_failed.complete'] = perf_counter()

            else:
                self.timers[
                    'qitem.aexit.mark_failed.start'] = perf_counter()
                #await mark_failed(self.conn, self.nid, self.username,
                #                  self.transport)
                self.timers[
                    'qitem.aexit.mark_failed.complete'] = perf_counter()
            self.logger.debug('returning qitem to q', qid=self.qitem['qid'])
        else:
            self.timers[
                'qitem.aexit.commit.start'] = perf_counter()
            await self.tx.commit()
            self.timers[
                'qitem.aexit.commit.complete'] = perf_counter()
            self.timers[
                'qitem.aexit.mark_sent.start'] = perf_counter()
            await mark_sent(self.conn,self.nid, self.username, self.transport)
            self.timers[
                'qitem.aexit.mark_failed.complete'] = perf_counter()
            self.logger.debug('deleted qitem from q', qid=self.qitem['qid'])

        self.timers['qitem.aexit.complete'] = perf_counter()

def worker_factory(database_url:str,
                         q_visibility_timeout:int=5,
                         worker_func=None,
                         worker_func_kwargs=None):
    worker_func_kwargs = worker_func_kwargs or dict()
    async def q_worker(database_url,
                       q_visibility_timeout,
                       worker_func,
                       worker_func_kwargs):
        idle_in_transaction_session_timeout = q_visibility_timeout * 1000
        conn = await yo.db.create_asyncpg_conn(database_url, server_settings={'idle_in_transaction_session_timeout':str(idle_in_transaction_session_timeout)})
        local_logger = logger.bind()
        timers = {'loop_start':perf_counter()}
        while True:
            async with QItem(conn, local_logger) as qitem:
                timers['qitem.receive'] = perf_counter()
                if not qitem:
                    local_logger.debug('no qitem available')
                    await asyncio.sleep(0)  # yield to others
                    timers['qitem.empty'] = perf_counter()
                local_logger.debug('qitem marked invisible', qitem=qitem['qid'])
                timers['worker_func.start'] = perf_counter()
                await worker_func(qitem, local_logger, **worker_func_kwargs)
                timers['worker_func.complete'] = perf_counter()
                timers['qitem.processed'] = perf_counter()
            logger.debug('qitem processed',**timers)


    return lambda: q_worker(database_url,q_visibility_timeout,worker_func,worker_func_kwargs)
