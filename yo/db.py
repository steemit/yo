# coding=utf-8
import logging
import os

import sqlalchemy as sa

import aiomysql.sa
import json

from contextlib import contextmanager
logger = logging.getLogger('__name__')

metadata = sa.MetaData()

NOTIFICATION_TYPES=('vote')
TRANSPORT_TYPES   =('email')
PRIORITY_LEVELS   ={'always'   :5,
                    'priority' :4,
                    'normal'   :3,
                    'low'      :2,
                    'marketing':1}
# TODO - this should be done in a cleaner way
PRIORITY_ALWAYS    = 5
PRIORITY_PRIORITY  = 4
PRIORITY_NORMAL    = 3
PRIORITY_LOW       = 2
PRIORITY_MARKETING = 1


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

class YoDatabase:
   def __init__(self,config):
      provider = config.config_data['database'].get('provider','sqlite3')
      if provider=='sqlite':
         self.engine = sa.create_engine('sqlite:///%s' % config.config_data['sqlite'].get('filename',':memory:'))
      #TODO - add MySQL here
      if int(config.config_data['database'].get('init_schema',0))==1:
         metadata.create_all(self.engine)
      initdata_file = config.config_data['database'].get('init_data',None)
      if not (initdata_file is None):
         fd = open(initdata_file,'rb')
         jsondata = json.load(fd)
         fd.close()
         for entry in jsondata:
             table_name,data = entry
             if table_name=='user_transports_table':
                with acquire_db_conn(self.engine) as conn:
                     conn.execute(user_transports_table.insert(),**data)
             elif table_name=='notifications_table':
                with acquire_db_conn(self.engine) as conn:
                     conn.execute(notifications_table.insert(),**data)
   async def close(self):
       if 'close' in dir(self.engine):
          self.engine.close()
          await self.engine.wait_closed()

   @contextmanager
   def acquire_db_conn(db):
       conn = db.connect()
       try:
          yield conn
       finally:
          conn.close()

   def get_priority_count(self, to_username, priority,timeframe):
       """Returns count of notifications to a user of a set priority or higher

       This is used to implement the rate limits

       Args:
           db:               SQLAlchemy database engine
           to_username(str): The username to lookup
           priority(int):    The priority level to lookup
           timeframe(int):   The timeframe in seconds to check

       Returns:
           An integer count of the number of notifications sent to the specified user within the specified timeframe of that priority level or higher
       """
       start_time = datetime.datetime.now()- datetime.timedelta(seconds=timeframe)
       retval = 0
       with self.acquire_conn() as conn:
            try:
               select_response = conn.execute(notifications_table.select().where(to_username==to_username,priority_level>=priority,sent==True,sent_at>=start_time))
               retval = select_response.rowcount
            except:
               logger.exception('Exception occurred!')
       return retval

   def create_notification(self, **notification_object):
       """ Creates an unsent notification in the DB
       
       Args:
           db:                        SQLAlchemy database engine, usually available from the app object as yo_db
           notification_object(dict): the actual notification to create+store

       Returns:
          True on success, False on error
       """
       with self.acquire_conn() as conn:
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
