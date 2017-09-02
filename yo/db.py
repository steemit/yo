# coding=utf-8
import logging
import os

import sqlalchemy as sa

import aiomysql.sa
import json

logger = logging.getLogger('__name__')

metadata = sa.MetaData()

NOTIFICATION_TYPES=('vote')
TRANSPORT_TYPES   =('email')
PRIORITY_LEVELS   ={'always'   :5,
                    'priority' :4,
                    'normal'   :3,
                    'low'      :2,
                    'marketing':1}

notifications_table = sa.Table('yo_notifications', metadata,
     sa.Column('nid', sa.Integer, primary_key=True),
     sa.Column('trx_id', sa.String(40), index=True, nullable=False,
               doc='The trx_id from the blockchain'),
     sa.Column('json_data', sa.UnicodeText),

     sa.Column('to_username', sa.Unicode, index=True),
     sa.Column('from_username', sa.Unicode, index=True),

     sa.Column('type', sa.Enum(NOTIFICATION_TYPES), nullable=False, index=True),

     sa.Column('sent', sa.Boolean(), nullable=True, default=False, index=True),
     sa.Column('priority_level', sa.Integer, index=True),

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
user_transports_table = sa.Table('yo_user_configured_transports', metadata,
     sa.Column('tid', sa.Integer, primary_key=True),

     sa.Column('username', sa.Unicode, index=True),

     sa.Column('notify_type', sa.Enum(NOTIFICATION_TYPES), nullable=False, index=True),
     sa.Column('transport_type', sa.Enum(TRANSPORT_TYPES), nullable=False, index=True),

     sa.Column('sub_data', sa.Unicode, index=False),

     sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True,
               doc='Datetime when we first created this user preferences entry'),
     sa.Column('updated_at', sa.DateTime, default=sa.func.now(), index=True,
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

def create_notification(db, **notification_object):
    """ Creates an unsent notification in the DB
    
    Args:
        db:                        SQLAlchemy database engine, usually available from the app object as yo_db
        notification_object(dict): the actual notification to create+store

    Returns:
       True on success, False on error
    """
    with acquire_db_conn(db) as conn:
         retval = False
         try:
            tx = conn.begin()
            insert_response = conn.execute(notifications_table.insert(), **notification_object)
            tx.commit()
            retval = True
            logger.debug('Created new notification object: %s' % str(notification_object))
         except:
            tx.rollback()
            logger.error('Failed to create new notification object: %s' % str(notification_object))
    return retval

def init_db(config):
      provider = config.config_data['database'].get('provider','sqlite3')
      if provider=='sqlite':
         engine = sa.create_engine('sqlite:///%s' % config.config_data['sqlite'].get('filename',':memory:'))
      #TODO - add MySQL here
      if int(config.config_data['database'].get('init_schema',0))==1:
         metadata.create_all(engine)
      initdata_file = config.config_data['database'].get('init_data',None)
      if not (initdata_file is None):
         fd = open(initdata_file,'rb')
         jsondata = json.load(fd)
         fd.close()
         for entry in jsondata:
             table_name,data = entry
             if table_name=='user_transports_table':
                with acquire_db_conn(engine) as conn:
                     conn.execute(user_transports_table.insert(),**data)
             elif table_name=='notifications_table':
                with acquire_db_conn(engine) as conn:
                     conn.execute(notifications_table.insert(),**data)
      return engine

async def close_db(app):
    if 'close' in dir(app['config']['db']):
       app['config']['db'].close()
       await app['config']['db'].wait_closed()
