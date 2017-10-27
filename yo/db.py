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
logger = logging.getLogger(__name__)

metadata = sa.MetaData()

NOTIFY_TYPES = ('power_down', 'power_up', 'resteem', 'feed', 'reward', 'send', 'mention', 'follow', 'vote', 'comment_reply', 'post_reply', 'account_update', 'message', 'receive')

TRANSPORT_TYPES = ('email','sms','wwwpoll')

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
     sa.Column('notify_type', sa.String(20), nullable=False, index=True),
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

# TODO: at some point turn this back into a normalised SQL table and/or add logging so users can see when their settings were changed etc
user_settings_table = sa.Table('yo_user_settings', metadata,
     sa.Column('tid', sa.Integer, primary_key=True),
     sa.Column('username', sa.String(20), index=True),
     sa.Column('transports', sa.UnicodeText, index=False,
               doc='This is a JSON object used to store the transports, because denormalisation is more efficient right now'),
     sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=False,
               doc='Datetime when this user first used the service and thus first got settings configured'),
     sa.Column('updated_at', sa.DateTime, default=sa.func.now(), index=False,
               doc='Datetime when settings were last changed'),
     mysql_engine='InnoDB',
)

class YoDatabase:
   def __init__(self,config,initdata=None):
      db_url   = config.config_data['yo_general'].get('db_url','')
      if len(db_url)>0:
         logger.info('Connecting to user-provided database URL from DB_URL variable...')
         self.engine = sa.create_engine(db_url,pool_size=20)
      else:
         provider = config.config_data['database'].get('provider','sqlite')
         if provider=='sqlite':
            logger.info('Using sqlite engine for database storage')
            self.engine = sa.create_engine('sqlite:///%s' % config.config_data['sqlite'].get('filename',':memory:'))
         elif provider=='mysql':
            logger.info('Using MySQL provider to build SQLAlchemy URL')
            self.engine = sa.create_engine('mysql+pymysql://%s:%s@%s/%s?host=%s' % ( config.config_data['mysql'].get('username',''),
                                                                                     config.config_data['mysql'].get('password',''),
                                                                                     config.config_data['mysql'].get('hostname','127.0.0.1'),
                                                                                     config.config_data['mysql'].get('database','yo'),
                                                                                     config.config_data['mysql'].get('hostname','127.0.0.1')),pool_size=20)
      if int(config.config_data['database'].get('reset_db',0))==1:
         logger.info('Wiping old data due to YO_DATABASE_RESET_DB=1')
         metadata.drop_all(self.engine)
         logger.info('Finished wiping old data')
      if int(config.config_data['database'].get('init_schema',0))==1:
         logger.info('Creating/updating database schema...')
         metadata.create_all(self.engine)
      if initdata is None:
         initdata_file = config.config_data['database'].get('init_data',None)
         if initdata_file is None:
            logger.info('No initial data file specified, not loading initdata')
            initdata = []
         else:
            logger.info('Loading initdata from file %s' % initdata_file)
            fd = open(initdata_file,'rb')
            initdata = json.load(fd)
            fd.close()
            logger.info('Finished reading initdata file')
      logger.debug('Inserting %d items from initdata into database...' % len(initdata))
      for entry in initdata:
          table_name,data = entry
          with self.acquire_conn() as conn:
               for k,v in data.items():
                   if str(metadata.tables['yo_%s' % table_name].columns[k].type) == 'DATETIME':
                      data[k] = dateutil.parser.parse(v)
               conn.execute(metadata.tables['yo_%s' % table_name].insert(),**data)
      logger.debug('Finished inserting %d items from initdata' % len(initdata))
      logger.info('DB Layer ready')
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

   def get_user_transports(self, username):
       """Returns the JSON object representing user's configured transports

       This method does no validation on the object, it is assumed that the object was validated in set_user_transports

       Args:
          username(str): the username to lookup

       Returns:
          str: the transports configured for the user
       """
       retval = None # TODO - as soon as we have a proper error specification, use it here
       with self.acquire_conn() as conn:
            query = user_settings_table.select().where(user_settings_table.c.username == username)
            select_response = conn.execute(query)
            json_settings = select_response.fetchone()['transports']
            print('JSON dump: %s' % str(json_settings))
            retval = json.loads(json_settings)
       return retval


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
