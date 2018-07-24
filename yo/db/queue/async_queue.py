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
