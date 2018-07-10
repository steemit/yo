# -*- coding: utf-8 -*-
import asyncio
import dateutil
import dateutil.parser
import sqlalchemy as sa
import structlog
import toolz

from asyncio.queues import Queue


from sqlalchemy.dialects.postgresql import JSONB
import asyncpg

logger = structlog.getLogger(__name__, source='YoDB')

from yo.db import metadata
from ..schema import TransportType

PUSH_Q_STMT = '''
INSERT INTO queue(data,transport,done) VALUES($1,$2,FALSE) RETURNING id
'''


POP_Q_STMT = '''
DELETE FROM queue
WHERE id = (
  SELECT id
  FROM queue
  WHERE transport = $1
  ORDER BY id
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
RETURNING id, data;
'''

Q_SIZE_STMT = '''
SELECT COUNT(*) FROM queue;
'''

Q_SIZE_FOR_TRANSPORT_STMT = '''
SELECT COUNT(*) FROM queue WHERE transport = $1;
'''

queue = sa.Table(
    'queue',
    metadata,
    sa.Column('id', sa.BigInteger(), primary_key=True),
    sa.Column('data', JSONB(), index=False, nullable=False),
    sa.Column('transport', sa.Integer(), index=True),
    sa.Column('done', sa.Boolean, index=True, nullable=False)
)

async def put(conn, data:dict, transport_type:TransportType) ->int:
    logger.debug(f'enqueing {data["nid"]} for transport type {transport_type.name}')
    return await conn.fetchval(PUSH_Q_STMT, data, transport_type.value)


async def get(conn, transport_type:TransportType) -> asyncpg.Record:
    return await conn.fetchrow(POP_Q_STMT, transport_type.value)


async def size(conn, transport_type:TransportType) -> int:
    if transport_type:
        return await conn.fetchval(Q_SIZE_FOR_TRANSPORT_STMT, transport_type.value)
    return await conn.fetchval(Q_SIZE_STMT)


class QItem:
    __slots__ = ('transport_type', 'conn', 'tx', 'conn','qitem',)

    def __init__(self, conn, transport_type):
        self.conn = conn
        self.transport_type = transport_type
        self.tx = None
        self.qitem = None

    async def __aenter__(self):
        #self.conn = await self.pool.acquire()
        while await size(self.conn, self.transport_type) <= 0:
            await asyncio.sleep(0)
        self.tx = self.conn.transaction()
        await self.tx.start()
        while True:
            row = await self.conn.fetchrow(POP_Q_STMT, self.transport_type)
            if not row: # item might have been removed before we got it
                await asyncio.sleep(0)
                continue
            logger.debug('q query returned row', item=row)
            break
        self.qitem = row
        logger.debug('passing q item to worker', itemid=self.qitem['id'],
                     transport=self.transport_type)
        return self.qitem['data']

    async def __aexit__(self, extype, ex, tb):
        if extype is not None:
            await self.tx.rollback()
            logger.debug('rolling back, leaving item on q', itemid=self.qitem['id'])
        else:
            await self.tx.commit()
            logger.debug('committing, item deleted from q', itemid=self.qitem['id'])



class QueueStorage:
    '''A mixin class to preservice compatability with asyncio.Queue which
    calls len(self._queue)
    '''
    def __init__(self, loop, pool, transport_type:TransportType):
        self.loop = loop
        self.pool = pool
        self.transport_type = transport_type

    def __len__(self) -> int:
        return self.loop.run_until_complete(size(self.pool, self.transport_type))

class WorkQueue(Queue):

    def __init__(self, loop=None, pool=None, transport_type:TransportType=None):
        self.pool = pool
        self.transport_type = transport_type
        super().__init__(loop=loop)

    def _init(self, maxsize):
        self._queue = QueueStorage(self._loop, self.pool, self.transport_type)

    def _get(self):
        return self._loop.run_until_complete(get(self.pool, self.transport_type))

    def _put(self, item):
        return self._loop.run_until_complete(
            put(self.pool, data=item, transport_type=self.transport_type))





