# -*- coding: utf-8 -*-

import sqlalchemy as sa
import structlog
import toolz


logger = structlog.getLogger(__name__, source='YoDB')

from yo.db import metadata
from ..schema import NotificationType


desktop = sa.Table(
    'desktop',
    metadata,
    sa.Column('dnid', sa.BigInteger(), primary_key=True),
    sa.Column('eid', sa.Text()),
    sa.Column('notify_type', sa.Integer(), nullable=False),
    sa.Column('to_username',sa.Text(),nullable=False, index=True),
    sa.Column('from_username',sa.Text(),nullable=True),
    sa.Column('json_data', sa.UnicodeText()),
    sa.Column('created', sa.DateTime, nullable=False),
    sa.Column('shown', sa.DateTime, nullable=True),
    sa.Column('read', sa.DateTime, nullable=True),
    sa.Index('ix_desktop','to_username','shown','read')
)

CREATE_STMT = '''
INSERT INTO desktop(eid, notify_type, to_username, from_username, json_data, created)
VALUES ($1, $2, $3, $4, $5, NOW())
RETURNING dnid
'''

GET_STMT = '''
SELECT * FROM desktop where to_username == $1 and shown = $2 and read = $3
'''

MARK_SHOWN_STMT = '''
UPDATE desktop SET shown = NOW() WHERE dnid = $1
'''

MARK_READ_STMT = '''
UPDATE desktop SET read = NOW() WHERE dnid = $1
'''

MARK_UNSHOWN_STMT = '''
UPDATE desktop SET shown = NULL WHERE dnid = $1
'''

MARK_UNREAD_STMT = '''
UPDATE desktop SET read = NULL WHERE dnid = $1
'''

async def create_desktop_notification(conn,
                                      eid:str=None,
                                      notify_type:NotificationType=None,
                                      to_username:str=None,
                                      from_username:str=None,
                                      json_data:dict=None) -> int:
    return await conn.fetchval(CREATE_STMT, eid, notify_type, to_username, from_username, json_data)

async def get_user_desktop_notifications(pool, username:str, read=None, shown=None):
    return await pool.fetch(GET_STMT, username, read, shown)

async def mark_shown(pool, dnid):
    return await pool.execute(MARK_SHOWN_STMT, dnid)

async def mark_read(pool, dnid):
    return await pool.execute(MARK_READ_STMT, dnid)

async def mark_unshown(pool, dnid):
    return await pool.execute(MARK_UNSHOWN_STMT, dnid)

async def mark_unread(pool, dnid):
    return await pool.execute(MARK_UNREAD_STMT, dnid)

