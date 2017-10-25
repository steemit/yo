# coding=utf-8
import logging
import os

import sqlalchemy as sa
import datetime

import dateutil
import dateutil.parser

import aiomysql.sa
import json

import enum

from contextlib import contextmanager
logger = logging.getLogger('__name__')

metadata = sa.MetaData()

NOTIFICATION_TYPES = ('vote')

TRANSPORT_TYPES = ('email','sms','polled')

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



# This is the table queried by API server for the wwwpoll transport
wwwpoll_table = sa.Table('yo_wwwpoll', metadata,

     sa.Column('notify_id', sa.Integer, primary_key=True),
     sa.Column('notify_type', sa.String(10), nullable=False, index=True),
     sa.Column('created', sa.DateTime, index=True),
     sa.Column('updated', sa.DateTime, index=True),
     sa.Column('read',sa.Boolean(), nullable=True, default=False),
     sa.Column('seen',sa.Boolean(), nullable=True, default=False),
     sa.Column('username',sa.String(20), index=True),
     sa.Column('data',sa.UnicodeText),

     mysql_engine='InnoDB',
)

# This is where ALL notifications go, not to be confused with the wwwpoll transport specific table above
notifications_table = sa.Table('yo_notifications', metadata,
     sa.Column('nid', sa.Integer, primary_key=True),
     sa.Column('trx_id', sa.String(40), index=True, nullable=False,
               doc='The trx_id from the blockchain'),
     sa.Column('json_data', sa.UnicodeText),

     sa.Column('to_username',   sa.String(20), index=True),
     sa.Column('from_username', sa.String(20), index=True),

     sa.Column('type', sa.String(10), nullable=False, index=True),

     sa.Column('sent', sa.Boolean(), nullable=True, default=False, index=True),
     sa.Column('priority_level', sa.Integer, index=True),

     sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True,
               doc='Datetime when notification was created and stored in db'),
     sa.Column('sent_at', sa.DateTime, index=True,
               doc='Datetime when notification was sent'),
     mysql_engine='InnoDB',
)

# We basically just store one entry for each configured transport, and delete them with API calls if required
user_transports_table = sa.Table('yo_user_transports', metadata,
     sa.Column('tid', sa.Integer, primary_key=True),

     sa.Column('username', sa.String(20), index=True),

     sa.Column('notify_type', sa.String(10), nullable=False, index=True),
     sa.Column('transport_type', sa.String(10), nullable=False, index=True),

     sa.Column('sub_data', sa.String(1024), index=False),

     sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True,
               doc='Datetime when we first created this user preferences entry'),
     sa.Column('updated_at', sa.DateTime, default=sa.func.now(), index=True,
               doc='Datetime when preferences were updated'),
     mysql_engine='InnoDB',
)

# bad practice i know, single row
block_status_table = sa.Table('yo_block_status', metadata,
     sa.Column('last_processed_block', sa.Integer),
)

class YoDatabase:
   def __init__(self,config,initdata=None):
      provider = config.config_data['database'].get('provider','sqlite')
      if provider=='sqlite':
         self.engine = sa.create_engine('sqlite:///%s' % config.config_data['sqlite'].get('filename',':memory:'))
      elif provider=='mysql':
         self.engine = sa.create_engine('mysql+pymysql://%s:%s@%s/%s?host=%s' % ( config.config_data['mysql'].get('username',''),
                                                                                  config.config_data['mysql'].get('password',''),
                                                                                  config.config_data['mysql'].get('hostname','127.0.0.1'),
                                                                                  config.config_data['mysql'].get('database','yo'),
                                                                                  config.config_data['mysql'].get('hostname','127.0.0.1')),pool_size=20)
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
               for k,v in data.items():
                   if str(metadata.tables['yo_%s' % table_name].columns[k].type) == 'DATETIME':
                      data[k] = dateutil.parser.parse(v)
               conn.execute(metadata.tables['yo_%s' % table_name].insert(),**data)
   async def close(self):
       if 'close' in dir(self.engine): # pragma: no cover
          self.engine.close()
          await self.engine.wait_closed()

   @contextmanager
   def acquire_conn(self):
       conn = self.engine.connect()
       try:
          yield conn
       finally:
          conn.close()

   @contextmanager
   def start_tx(self):
       conn = self.engine.connect()
       tx   = conn.begin()
       try:
          yield tx
       except:
          tx.rollback()
       finally:
          conn.close()

   def get_wwwpoll_notifications(self, username=None, created_before=None, updated_after=None, read=None, notify_types=None, limit=30):
       """Returns an SQLAlchemy result proxy with the notifications stored in wwwpoll table matching the specified params

       Keyword args:
          username(str):       the username to lookup notifications for
          created_before(str): ISO8601-formatted timestamp
          updated_after(str):  ISO8601-formatted
          read(bool):          if set, only return notifications where the read flag is set to this value
          notify_types(list):  if set, only return notifications of one of the types specified in this list
          limit(int):          return at most this number of notifications

       Returns:
          SQLAlchemy result proxy from the select query
       """
       with self.acquire_conn() as conn:
            query = wwwpoll_table.select()
            if not (username is None):
               query = query.where(wwwpoll_table.c.username == username)
            if not (created_before is None):
               created_before_val = dateutil.parser.parse(created_before)
               query = query.where(wwwpoll_table.c.created >= created_before_val)
            if not (updated_after is None):
               updated_after_val = dateutil.parser.parse(updated_after)
               query = query.where(wwwpoll_table.c.updated <= updated_after_val)
            if not (read is None):
               query = query.where(wwwpoll_table.c.read == read)
            if not (notify_types is None):
               query = query.filter(wwwpoll_table.c.notify_type.in_(notify_types))
            query = query.limit(limit)
            resp = conn.execute(query)
       return resp     

   def get_user_transports(self, username, notify_type=None, transport_type=None):
       """Returns an SQLAlchemy result proxy with all the user transports enabled for specified username

       Args:
          username(str): the username to lookup
       
       Keyword args:
          notify_type(str):    if set, returns only the configured transports for the specified notify_type
          transport_type(str): if set, returns the configured transports of that type only

       Returns:
          SQLAlchemy result proxy from the select query
       """
       # TODO - make this return a more general-purpose iterator or something
       with self.acquire_conn() as conn:
            query = user_transports_table.select().where(user_transports_table.c.username == username)
            if not (notify_type is None):
               query = query.where(user_transports_table.c.notify_type==notify_type)
            if not (transport_type is None):
               query = query.where(user_transports_table.c.transport_type==transport_type)
            select_response = conn.execute(query)
       return select_response

   def update_subdata(self, username, transport_type=None, notify_type=None, sub_data=None):
       """Updates sub_data field for selected transport

       If the transport record does not exist, it is created

       Args:
          username(str): the user to update

       Keyword args:
          transport_type(str): the transport type to update
          notify_type(str):    the notification type to update
          sub_data(str):       the sub_data (subscription data)
       """
       # first check if the transport already exists or not
       existing_transports = self.get_user_transports(username,notify_type=notify_type,transport_type=transport_type).fetchall()
       if len(existing_transports)>0: # transport exists, we need to update it
          update_query = user_transports_table.update().values(sub_data=sub_data)
          update_query = update_query.where(user_transports_table.c.username==username)
          update_query = update_query.where(user_transports_table.c.notify_type==notify_type)
          update_query = update_query.where(user_transports_table.c.transport_type==transport_type)
       else: # doesn't exist, we need to create it
          update_query = user_transports_table.insert().values(username=username,
                                                               notify_type=notify_type,
                                                               transport_type=transport_type,
                                                               sub_data=sub_data)
       with self.acquire_conn() as conn:
            conn.execute(update_query)

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
