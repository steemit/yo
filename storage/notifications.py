# coding=utf-8
import logging
import os

import sqlalchemy as sa

from storage import metadata

log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'))
logging.basicConfig(level=log_level)
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
    'sent'
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

notifications_table = sa.Table('yo_notifications', metadata,
                 sa.Column('id', sa.Integer, primary_key=True),
                 sa.Column('data', sa.Text),
                 sa.Column('status', sa.Enum(NOTIFICATION_STATUS), nullable=False),
                 sa.Column('to', sa.String(255), nullable=False, index=True),
                 sa.Column('from', sa.String(255)),
                 sa.Column('type', sa.Enum(NOTIFICATION_TYPES), nullable=False, index=True),
                 sa.Column('transport', sa.Enum(TRANSPORT_TYPES), nullable=False, index=True),
                 sa.Column('source_event', sa.String(255)),
                 sa.Column('created_at', sa.DateTime(timezone=False), nullable=False, index=True)
)

async def put(pool, table, notification):
    with (await pool) as conn:
        return await conn.execute(table.insert(), **notification)


async def get(pool, table, notification_id):
    with (await pool) as conn:
        query = table.select().where(table.c.id == notification_id)
        return await query.execute()


async def fetch_for_user(pool, table, username):
    with (await pool) as conn:
        query = table.select().where(table.c.to == username)
        return await query.execute()


async def mark_sent(pool, table, notification_id):
    with (await pool) as conn:
        query = table.update().where(table.c.id == notification_id).value(status='sent')
        return await query.execute()


async def mark_cancelled(pool, table, notification_id):
    with (await pool) as conn:
        query = table.update().where(table.c.id == notification_id).value(status='cancelled')
        return await query.execute()
