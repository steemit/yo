# coding=utf-8
import logging
import os

import sqlalchemy as sa

import aiomysql.sa


logger = logging.getLogger('__name__')

metadata = sa.MetaData()

NOTIFICATION_TYPES=('vote')
TRANSPORT_TYPES   =('sendgrid')

notifications_table = sa.Table('yo_notifications', metadata,
     sa.Column('nid', sa.Integer, primary_key=True),
     sa.Column('trx_id', sa.String(40), index=True, unique=True, nullable=False,
               doc='The trx_id from the blockchain'),
     sa.Column('json_data', sa.UnicodeText),

     sa.Column('to_username', sa.Unicode, index=True),
     sa.Column('from_username', sa.Unicode, index=True),

     sa.Column('type', sa.Enum(NOTIFICATION_TYPES), nullable=False, index=True),

     sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True,
               doc='Datetime when notification was created and stored in db'),
     sa.Column('sent_at', sa.DateTime, index=True,
               doc='Datetime when notification was sent'),
     sa.Column('seen_at', sa.DateTime, index=True,
               doc='Datetime when notification was seen (may be identical to read_at for some notification types)'),
     sa.Column('read_at', sa.DateTime, index=True,
               doc='Datetime when notification was read or marked as read'),
)

# We basically just store one entry for each configured transport, and delete them with API calls if required
preferences_table = sa.Table('yo_user_configured_transports', metadata,
     sa.Column('uid', sa.Integer, primary_key=True),

     sa.Column('username', sa.Unicode, index=True),

     sa.Column('notify_type', sa.Enum(NOTIFICATION_TYPES), nullable=False, index=True),
     sa.Column('transport_type', sa.Enum(NOTIFICATION_TYPES), nullable=False, index=True),

     sa.Column('sub_data', sa.Unicode, index=False),

     sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True,
               doc='Datetime when we first created this user preferences entry'),
     sa.Column('updated_at', sa.DateTime, index=True,
               doc='Datetime when preferences were updated'),
)

from contextlib import contextmanager
@contextmanager
def acquire_db_conn(db):
    conn = db.connect()
    try:
       yield conn
    finally:
       conn.close()

def init_db(config):
      provider = config.config_data['database'].get('provider','sqlite3')
      if provider=='sqlite':
         engine = sa.create_engine('sqlite:///%s' % config.config_data['sqlite'].get('filename',':memory:'))
      #TODO - add MySQL here
      if int(config.config_data['database'].get('init_schema',0))==1:
         metadata.create_all(engine)
      return engine

async def close_db(app):
    if 'close' in dir(app['config']['db']):
       app['config']['db'].close()
       await app['config']['db'].wait_closed()
