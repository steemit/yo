# coding=utf-8
import logging
import os
import asyncio
from datetime import datetime
from datetime import timedelta

import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy.schema import ForeignKey




from storage import metadata

logger = logging.getLogger('__name__')



TRANSPORT_TYPES = (
    'email',
    'sms',
    'browser',
    'web'
)

NOTIFICATION_TYPES = (
    'total',
    'feed',
    'reward',
    'send',
    'mention',
    'follow',
    'vote',
    'comment_reply',
    'post_reply',
    'account_update',
    'message',
    'receive'
)

NOTIFICATION_STATUS = (
    'created',
    'sent',
    'seen',
    'read'
)

'''
Event JSON Schema
-----------------
{
  "id": "https://schema.steemitdev.com/notifications/notification.json#",
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "Schema For Steemit Notifications",
  "type": "object",
  "required": [
    "data",
    "id",
    "status",
    "created_at",
    "source_event",
    "to",
    "type",
    "transport"
  ],
  "properties": {
    "transport": {
      "enums": [
        "email",
        "sms",
        "browser",
        "web"
      ],
      "type": "string"
    },
    "id": {
      "type": "string"
    },
    "to": {
      "$ref": "#/definitions/account_name_type"
    },
    "status": {
      "enums": [
        "created",
        "sent"
      ],
      "type": "string"
    },
    "source_event": {
      "type": "string"
    },
    "type": {
      "enums": [
        "total",
        "feed",
        "reward",
        "send",
        "mention",
        "follow",
        "vote",
        "comment_reply",
        "post_reply",
        "account_update",
        "message",
        "receive"
      ],
      "type": "string"
    },
    "from": {
      "anyOf": [
        {
          "$ref": "#/definitions/account_name_type"
        },
        {
          "type": "string"
        }
      ]
    },
    "data": {
      "type": "object"
    },
    "created_at": {
      "format": "date-time",
      "type": "string"
    }
  },
  "definitions": {
    "account_name_type": {
      "minLength": 3,
      "description": "https://github.com/steemit/steem/blob/master/libraries/protocol/include/steemit/protocol/config.hpp#L207",
      "type": "string",
      "maxLength": 16
    }
  }
}
'''

table = sa.Table('yo_notifications', metadata,
     sa.Column('nid', sa.Integer, primary_key=True),
     sa.Column('data', sa.UnicodeText),

     # yo_users.uid
     sa.Column('to', sa.Integer, ForeignKey('yo_users.uid'), nullable=False, index=True),

     # yo_users.uid
     sa.Column('from', sa.Integer, ForeignKey('yo_users.uid'), index=True),

     sa.Column('type', sa.Enum(NOTIFICATION_TYPES), nullable=False, index=True),
     sa.Column('transport', sa.Enum(TRANSPORT_TYPES), nullable=False, index=True),
     sa.Column('source_event', sa.String(255)),

    sa.Column('created_at', sa.DateTime, default=func.now(), index=True,
              doc='Datetime when notification was created and stored in db'),
    sa.Column('sent_at', sa.DateTime, index=True,
              doc='Datetime when notification was sent'),
    sa.Column('seen_at', sa.DateTime, index=True,
              doc='Datetime when notification was seen (may be identical to read_at for some notification types)'),
    sa.Column('read_at', sa.DateTime, index=True,
              doc='Datetime when notification was read or marked as read'),

)

async def put(engine, notification):
    async with engine.acquire() as conn:
        return await conn.execute(table.insert(), **notification)


async def get(engine, notification_id):
    async with engine.acquire() as conn:
        query = table.select().where(table.c.nid == notification_id)
        return await query.execute().first()


async def fetch_for_user(engine, uid):
    async with engine.acquire() as conn:
        query = table.select().where(table.c.to == uid)
        return await query.execute().first()


async def mark_sent(engine, notification_id):
    async with engine.acquire() as conn:
        query = table.update().where(table.c.id == notification_id).value(sent_at=func.now())
        return await query.execute()


async def mark_seen(engine, notification_id):
    async with engine.acquire() as conn:
        stmt = table.update().where(table.c.id == notification_id).value(seen_at=func.now())
        return await stmt.execute()


async def mark_read(engine, notification_id):
    async with engine.acquire() as conn:
        stmt = table.update().where(table.c.id == notification_id).value(read_at=func.now())
        return await conn.execute(stmt)


async def status(engine, notification_id):
    async with engine.acquire() as conn:
        query = table.select().where(table.c.nid == notification_id)
        notification =  await query.execute().first()
        return await notification_status(notification)


async def count_recent(engine, uid, hours=24):
    async with engine.acquire() as conn:
        min_datetime = datetime.utcnow() - timedelta(hours=hours)
        query = table.select([table.c.type, func.count('*')]).where(table.c.uid == uid)
        query = query.where(table.c.sent_at > min_datetime)
        query = query.group_by(table.c.type)
        return await query.execute().fetchall()



async def notification_status(notification):
    if not notification:
        return None
    if notification['read_at']:
        return 'read'
    elif notification['seen_at']:
        return 'seen'
    elif notification['sent_at']:
        return 'sent'
    else:
        return 'created'