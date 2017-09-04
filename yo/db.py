# coding=utf-8
import logging
import os

import sqlalchemy as sa
import datetime

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
user_transports_table = sa.Table('yo_user_transports', metadata,
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
   def __init__(self,config,initdata=None):
      provider = config.config_data['database'].get('provider','sqlite3')
      if provider=='sqlite':
         self.engine = sa.create_engine('sqlite:///%s' % config.config_data['sqlite'].get('filename',':memory:'))
      #TODO - add MySQL here
      if int(config.config_data['database'].get('init_schema',0))==1:
         metadata.create_all(self.engine)
      if initdata is None:
         initdata_file = config.config_data['database'].get('init_data',None)
         if initdata_file is None:
            initdata = []
         else:
            fd = open(initdata_file,'rb')
            initdata = json.load(fd)
            fd.close()
      for entry in initdata:
          table_name,data = entry
          with self.acquire_conn() as conn:
               conn.execute(metadata.tables['yo_%s' % table_name].insert(),**data)
   async def close(self):
       if 'close' in dir(self.engine):
          self.engine.close()
          await self.engine.wait_closed()

   @contextmanager
   def acquire_conn(self):
       conn = self.engine.connect()
       try:
          yield conn
       finally:
          conn.close()

   def get_user_transports(self, username, notify_type=None):
       """Returns an SQLAlchemy result proxy with all the user transports enabled for specified username

       Args:
          username(str): the username to lookup
       
       Keyword args:
          notify_type(str): if set, returns only the configured transports for the specified notify_type

       Returns:
          SQLAlchemy result proxy from the select query
       """
       # TODO - make this return a more general-purpose iterator or something
       with self.acquire_conn() as conn:
            query = user_transports_table.select().where(user_transports_table.c.username == username)
            if not (notify_type is None):
               query = query.where(user_transports_table.c.notify_type==notify_type)
            select_response = conn.execute(query)
       return select_response

   def get_priority_count(self, to_username, priority, timeframe, start_time=None):
       """Returns count of notifications to a user of a set priority or higher

       This is used to implement the rate limits

       Args:
           db:               SQLAlchemy database engine
           to_username(str): The username to lookup
           priority(int):    The priority level to lookup
           timeframe(int):   The timeframe in seconds to check

       Keyword args:
           start_time(datetime.datetime): the current time to go backwards from, if not set datetime.now() will be used

       Returns:
           An integer count of the number of notifications sent to the specified user within the specified timeframe of that priority level or higher
       """
       if start_time is None:
          start_time = datetime.datetime.now()- datetime.timedelta(seconds=timeframe)
       retval = 0
       with self.acquire_conn() as conn:
            try:
               query = notifications_table.select().where(notifications_table.c.to_username==to_username)
               query = query.where(notifications_table.c.priority_level>=priority)
               query = query.where(notifications_table.c.sent==True)
               query = query.where(notifications_table.c.sent_at>=start_time)
               select_response = conn.execute(query)
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
