# coding=utf-8
import datetime
import json
import logging
import uuid
from contextlib import contextmanager

import dateutil
import dateutil.parser
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlite3 import IntegrityError as SQLiteIntegrityError
logger = logging.getLogger(__name__)

metadata = sa.MetaData()

NOTIFY_TYPES = ('power_down', 'power_up', 'resteem', 'feed', 'reward', 'send',
                'mention', 'follow', 'vote', 'comment_reply', 'post_reply',
                'account_update', 'message', 'receive')


TRANSPORT_TYPES = ('email', 'sms', 'wwwpoll')

PRIORITY_LEVELS = {
    'always': 5,
    'priority': 4,
    'normal': 3,
    'low': 2,
    'marketing': 1
}
# TODO - this should be done in a cleaner way
PRIORITY_ALWAYS = 5
PRIORITY_PRIORITY = 4
PRIORITY_NORMAL = 3
PRIORITY_LOW = 2
PRIORITY_MARKETING = 1




DEFAULT_USER_TRANSPORT_SETTINGS = {
                "email": {
                    "notification_types": [],
                    "sub_data": {}
                },
                "wwwpoll": {
                    "notification_types": [
                        "power_down",
                        "power_up",
                        "resteem",
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
                    "sub_data": {}
                }
            }

DEFAULT_USER_TRANSPORT_SETTINGS_STRING = json.dumps(DEFAULT_USER_TRANSPORT_SETTINGS)


# This is the table queried by API server for the wwwpoll transport
wwwpoll_table = sa.Table(
    'yo_wwwpoll',
    metadata,
    sa.Column(
        'notify_id', sa.String(36), primary_key=True
    ),  # TODO - look into whether this really does cause performance issues
    sa.Column('notify_type', sa.String(20), nullable=False, index=True),
    sa.Column('created', sa.DateTime, index=True),
    sa.Column('updated', sa.DateTime, index=True),
    sa.Column('read', sa.Boolean(), default=False),
    sa.Column('seen', sa.Boolean(), default=False),
    sa.Column('username', sa.String(20), index=True),
    sa.Column('data', sa.UnicodeText),
    sa.UniqueConstraint('username','notify_type','data',name='yo_wwwpoll_idx'),
    mysql_engine='InnoDB',
)

# This is where ALL notifications go, not to be confused with the wwwpoll transport specific table above
notifications_table = sa.Table(
    'yo_notifications',
    metadata,
    sa.Column('nid', sa.Integer, primary_key=True),
    sa.Column(
        'trx_id',
        sa.String(40),
        index=True,
        nullable=True,
        doc='The trx_id from the blockchain'),
    sa.Column('json_data', sa.UnicodeText),
    sa.Column('to_username', sa.String(20), nullable=False, index=True),
    sa.Column('from_username', sa.String(20), index=True, nullable=True),
    sa.Column('type', sa.String(10), nullable=False, index=True),
    sa.Column('sent', sa.Boolean(), nullable=False, default=False, index=True),
    sa.Column('priority_level', sa.Integer, index=True, default=3),
    sa.Column(
        'created_at',
        sa.DateTime,
        default=sa.func.now(),
        index=True,
        doc='Datetime when notification was created and stored in db'),
    sa.Column(
        'sent_at',
        sa.DateTime,
        index=True,
        doc='Datetime when notification was sent'),
    sa.UniqueConstraint('to_username','type','trx_id','from_username','json_data', name='yo_notification_idx'),
    mysql_engine='InnoDB',
)

# TODO: at some point turn this back into a normalised SQL table and/or add logging so users can see when their settings were changed etc
user_settings_table = sa.Table(
    'yo_user_settings',
    metadata,
    sa.Column('tid', sa.Integer, primary_key=True),
    sa.Column('username', sa.String(20), unique=True),
    sa.Column(
        'transports',
        sa.UnicodeText,
        index=False,
        default=DEFAULT_USER_TRANSPORT_SETTINGS_STRING,
        nullable=False
    ),
    sa.Column(
        'created_at',
        sa.DateTime,
        default=sa.func.now(),
        index=False,
        doc=
        'Datetime when this user first used the service and thus first got settings configured'
    ),
    sa.Column(
        'updated_at',
        sa.DateTime,
        default=sa.func.now(),
        index=False,
        doc='Datetime when settings were last changed'),
    mysql_engine='InnoDB',
)


def is_duplicate_entry_error(error):
    if isinstance(error, (IntegrityError, SQLiteIntegrityError)):
        msg = str(error).lower()
        return "unique" in msg
    return False



class YoDatabase:
    def __init__(self, db_url=None):

        self.engine = sa.create_engine(db_url)

        logger.info('DB Layer ready')

    @contextmanager
    def acquire_conn(self):
        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close()


    def get_wwwpoll_notifications(self,
                                  username=None,
                                  created_before=None,
                                  updated_after=None,
                                  read=None,
                                  notify_types=None,
                                  limit=30):
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
            try:
                query = wwwpoll_table.select()
                if not (username is None):
                    query = query.where(wwwpoll_table.c.username == username)
                if not (created_before is None):
                    created_before_val = dateutil.parser.parse(created_before)
                    query = query.where(
                        wwwpoll_table.c.created >= created_before_val)
                if not (updated_after is None):
                    updated_after_val = dateutil.parser.parse(updated_after)
                    query = query.where(
                        wwwpoll_table.c.updated <= updated_after_val)
                if not (read is None):
                    query = query.where(wwwpoll_table.c.read == read)
                if not (notify_types is None):
                    query = query.filter(
                        wwwpoll_table.c.notify_type.in_(notify_types))
                query = query.limit(limit)
                return conn.execute(query)
            except:
                logger.exception('get_wwwpoll_notifications failed')
        return None

    def create_user(self, username):
        with self.acquire_conn() as conn:
            try:
                stmt = user_settings_table.insert(values={'username':username})
                return conn.execute(stmt)
            except:
                logger.exception('create_user failed')
                return None

    def set_user_transports(self, username, transports):
        """ Sets the JSON object representing user's configured transports

        This method does only basic sanity checks, it should only be invoked via the API server

        Args:
            username(str):    the user whose transports need to be set
            transports(dict): maps transports to dicts containing 'notification_types' and 'sub_data' keys
        """

        success = False
        with self.acquire_conn() as conn:
             query = user_settings_table.select().where(user_settings_table.c.username == username)
             old_resp  = conn.execute(query)
             now_time = datetime.now()
             if old_resp.row_count >0:
                settings_obj = dict(old_resp.fetchone()[0])
                del settings_obj['tid']
                settings_obj['updated_at'] = now_time
                settings_obj['transports'] = json.dumps(transports)
                query = user_settings_table.update().where(user_settings_table.c.username == username).values(**settings_obj)
             else:
                settings_obj = {'username'  :username,
                                'created_at':now_time,
                                'updated_at':now_time,
                                'transports':json.dumps(transports)}
                query = user_settings_table.update().where(user_settings_table.c.username == username)
             try:
                resp = conn.execute(query)
                success = True
             except:
                logger.exception('Exception occurred trying to update transports for user %s to %s' % (username,str(transports)))
        return {'success':success}

    def get_user_transports(self, username):
        """Returns the JSON object representing user's configured transports

       This method does no validation on the object, it is assumed that the object was validated in set_user_transports

       Args:
          username(str): the username to lookup

       Returns:
          dict: the transports configured for the user
       """

        with self.acquire_conn() as conn:
            try:
                query = user_settings_table.select().where(
                user_settings_table.c.username == username)
                select_response = conn.execute(query)
                results = select_response.fetchone()
                if results:
                    json_settings = results['transports']
                    return json.loads(json_settings)
                else:
                    logger.debug('no user found, creating new user')
                    self.create_user(username)
                    select_response = conn.execute(query)
                    results = select_response.fetchone()
                    print(results)
                    json_settings = results['transports']
                    return json.loads(json_settings)

            except:
                logger.exception('get_user_transports failed')
                return None

    def get_priority_count(self,
                           to_username,
                           priority,
                           timeframe,
                           start_time=None):
        """Returns count of notifications to a user of a set priority or higher

       This is used to implement the rate limits

       Args:
           to_username(str): The username to lookup
           priority(int):    The priority level to lookup
           timeframe(int):   The timeframe in seconds to check

       Keyword args:
           start_time(datetime.datetime): the current time to go backwards from, if not set datetime.now() will be used

       Returns:
           An integer count of the number of notifications sent to the specified user within the specified timeframe of that priority level or higher
           :param timeframe:
           :param priority:
           :param to_username:
           :param start_time:
       """
        if start_time is None:
            start_time = datetime.datetime.now() - datetime.timedelta(
                seconds=timeframe)
        retval = 0
        with self.acquire_conn() as conn:
            try:
                query = notifications_table.select().where(
                    notifications_table.c.to_username == to_username)
                query = query.where(
                    notifications_table.c.priority_level >= priority)
                query = query.where(notifications_table.c.sent == True)
                query = query.where(
                    notifications_table.c.sent_at >= start_time)
                select_response = conn.execute(query)
                retval = select_response.rowcount
            except:
                logger.exception('Exception occurred!')
        return retval

    def create_wwwpoll_notification(self,
                                    notify_id=None,
                                    notify_type=None,
                                    created_time=None,
                                    to_user=None,
                                    raw_data=None):
        """ Creates a new notification in the wwwpoll table

        Keyword Args:
           notify_id(str):    if not provided, will be autogenerated as a UUID
           notify_type(str):  the notification type
           created_time(str): ISO8601-formatted timestamp, if not set current time will be used
           raw_data(dict):    what to include in the data field of the stored notification, will be JSON-serialised for storage
           to_user(str):      the username we're sending to

        Returns:
           dict: the notification as stored in wwwpoll, None on error
        """
        if notify_id is None:
            notify_id = str(uuid.uuid1())
        if created_time is None:
            created_time = datetime.datetime.now()
        else:
            created_time = dateutil.parser.parse(created_time)

        notify_data = {
            'notify_id': notify_id,
            'notify_type': notify_type,
            'created': created_time,
            'updated': created_time,
            'read': False,
            'seen': False,
            'username': to_user,
            'data': json.dumps(raw_data)
        }
        with self.acquire_conn() as conn:
            success = False
            tx = conn.begin()
            try:
                insert_response = conn.execute(wwwpoll_table.insert(),
                                               **notify_data)
                tx.commit()
                success = True
                logger.debug('Created new wwwpoll notification object: %s' %
                             notify_data)
            except (IntegrityError, SQLiteIntegrityError) as e:
                if is_duplicate_entry_error(e):
                    logger.debug('Ignoring duplicate entry error')
                else:
                    logger.exception('failed to add notification')
                    tx.rollback()
            except:
                tx.rollback()
                logger.exception(
                    'Failed to create new wwwpoll notification object: %s' %
                    notify_data)
        if success:
            return notify_data

    def create_notification(self, **notification_object):
        """ Creates an unsent notification in the DB
       
        Keyword Args:
           notification_object(dict): the actual notification to create+store

        Returns:
          True on success, False on error
        """
        with self.acquire_conn() as conn:
            tx = conn.begin()
            try:
                _ = conn.execute(notifications_table.insert(),
                                               **notification_object)
                tx.commit()
                logger.debug('Created new notification object: %s',
                             notification_object)
                return True
            except Exception as e:
                if is_duplicate_entry_error(e):
                    logger.debug('Ignoring duplicate entry error')
                else:
                    logger.exception('failed to add notification')
                    tx.rollback()
        return False
