# -*- coding: utf-8 -*-

import sqlalchemy as sa
import structlog

from ..schema import ActionStatus
from ..schema import TransportType

from yo.db import metadata

logger = structlog.getLogger(__name__, source='YoDB')


PERMANENT_FAIL_COUNT = 3


actions_table = sa.Table(
    'actions',
    metadata,
    sa.Column('aid', sa.Integer, primary_key=True),
    sa.Column('nid',sa.BigInteger, sa.ForeignKey('notifications.nid')),
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

GET_NOTIFICATION_STATE = '''
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
  WITH sent as (
    SELECT created FROM actions WHERE username = $1 and transport = $2 and status = $3 and created >= NOW() - '1 day'::interval)
  SELECT COUNT(*) as cnt,date_trunc('hour',created) as hour FROM sent
  GROUP BY hour
'''


async def store(pool, nid, username, transport, status=None):
    return await pool.fetchval(INSERT_ACTION_STMT, nid, username, transport, status)


async def get_notification_state(pool, nid):
    return await pool.fetchrow(GET_NOTIFICATION_STATE, nid)



async def fail(pool, nid, transport):
    aid, nid, status = await pool.fetchrow(FAIL_ACTION_STMT,
                                              nid,
                                              transport,
                                              ActionStatus.failed,
                                              PERMANENT_FAIL_COUNT,
                                              ActionStatus.perm_failed)
    return aid, nid, status

async def rate_limited(pool, nid, username, transport):
    return await store(pool, nid, username, transport,
                 status=ActionStatus.rate_limited)

async def sent(pool, nid:int, username:str, transport:TransportType):
    return await store(pool, nid, username, transport,
                 status=ActionStatus.sent)


async def get_rates(pool, username:str, transport:TransportType,):
    rows = await pool.fetch(GET_RATES_STMT, username, transport, ActionStatus.sent.value)
