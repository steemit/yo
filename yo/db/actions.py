# -*- coding: utf-8 -*-
from typing import Tuple
from typing import TypeVar
import sqlalchemy as sa
import structlog

from asyncpg.pool import Pool
from asyncpg.connection import Connection


from ..schema import ActionStatus
from ..schema import TransportType

from yo.db import metadata

logger = structlog.getLogger(__name__, source='YoDB')

PoolOrConn = TypeVar('PoolOrConn', Pool, Connection)
ActionId = int
NotificationId = int

PERMANENT_FAIL_COUNT = 3


actions_table = sa.Table(
    'actions',
    metadata,
    sa.Column('aid', sa.BigInteger, primary_key=True),
    sa.Column('nid', sa.BigInteger),
    sa.Column('username', sa.Text(), index=True, nullable=False),
    sa.Column('transport', sa.Integer, nullable=False, index=True),
    sa.Column('status',sa.Integer,nullable=False,index=True),
    sa.Column('created', sa.DateTime, index=True)
)

INSERT_ACTION_STMT = '''
    INSERT INTO actions(nid, username, transport, status, created)
    VALUES ($1,$2,$3,$4,NOW())
    RETURNING aid
'''

GET_NOTIFICATION_STATE_STMT = '''
    SELECT status FROM actions WHERE nid=$1
    ORDER BY aid DESC
    LIMIT 1
'''

FAIL_ACTION_STMT = '''
  WITH fail_count AS (SELECT COUNT(*) FROM actions WHERE status = $4)
  INSERT INTO actions(nid, username, transport, status, created)
  VALUES($1, $2, $3,
    CASE WHEN fail_count >= $5 THEN $6
         ELSE $4
    END, NOW())
  RETURNING aid, nid, status
'''

GET_RATES_STMT = '''
  WITH mark_sent as (
    SELECT created FROM actions WHERE username = $1 and transport = $2 and status = $3 and created >= NOW() - '1 day'::interval)
  SELECT COUNT(*) as cnt,date_trunc('hour',created) as hour FROM mark_sent
  GROUP BY hour
'''

class RateLimitException(BaseException):
    pass

class PermanentFailException(BaseException):
    pass

class SendError(BaseException):
    pass

async def store(pool_or_conn:PoolOrConn, nid:int, username:str, transport:TransportType, status:ActionStatus) -> ActionId:
    return await pool_or_conn.fetchval(INSERT_ACTION_STMT, nid, username, transport, status)


async def get_notification_state(pool_or_conn:PoolOrConn, nid:int) -> ActionStatus:
    status_int = await pool_or_conn.fetchrow(GET_NOTIFICATION_STATE_STMT, nid)
    return ActionStatus(status_int)


async def mark_failed(pool_or_conn:PoolOrConn, nid:int, username:str, transport:TransportType) -> Tuple[ActionId, NotificationId, ActionStatus]:
    aid, nid, status = await pool_or_conn.fetchrow(FAIL_ACTION_STMT,
                                                   nid,
                                                   transport,
                                                   ActionStatus.failed,
                                                   PERMANENT_FAIL_COUNT,
                                                   ActionStatus.perm_failed)
    return aid, nid, status


async def mark_rate_limited(pool_or_conn:PoolOrConn, nid:int, username:str, transport:TransportType) -> ActionId:
    return await store(pool_or_conn, nid, username, transport,
                       status=ActionStatus.rate_limited)


async def mark_sent(pool_or_conn:PoolOrConn, nid:int, username:str, transport:TransportType) -> ActionId:
    return await store(pool_or_conn, nid, username, transport,
                       status=ActionStatus.sent)


async def get_rates(pool_or_conn:PoolOrConn, username:str, transport:TransportType, ):
    rows = await pool_or_conn.fetch(GET_RATES_STMT, username, transport, ActionStatus.sent.value)
    return rows
