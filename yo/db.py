# coding=utf-8
import datetime
import enum
import json
import logging
import uuid
from contextlib import contextmanager
from sqlite3 import IntegrityError as SQLiteIntegrityError

import dateutil
import dateutil.parser
import sqlalchemy as sa
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

metadata = sa.MetaData()

NOTIFY_TYPES = ('power_down', 'power_up', 'resteem', 'feed', 'reward', 'send',
                'mention', 'follow', 'vote', 'comment_reply', 'post_reply',
                'account_update', 'message', 'receive')

TRANSPORT_TYPES = ('email', 'sms', 'wwwpoll')


class Priority(enum.Enum):
    MARKETING = 1
    LOW = 2
    NORMAL = 3
    PRIORITY = 4
    ALWAYS = 5


DEFAULT_USER_TRANSPORT_SETTINGS = {
    "email": {
        "notification_types": [],
        "sub_data": {}
    },
    "wwwpoll": {
        "notification_types": [
            "power_down", "power_up", "resteem", "feed", "reward", "send",
            "mention", "follow", "vote", "comment_reply", "post_reply",
            "account_update", "message", "receive"
        ],
        "sub_data": {}
    }
}

DEFAULT_USER_TRANSPORT_SETTINGS_STRING = json.dumps(
    DEFAULT_USER_TRANSPORT_SETTINGS)

# This is the table queried by API server for the wwwpoll transport
wwwpoll_table = sa.Table(
    'yo_wwwpoll',
    metadata,
    sa.Column('nid', sa.String(36), primary_key=True),
    sa.Column('notify_type', sa.String(20), nullable=False, index=True),
    sa.Column('to_username', sa.String(20), nullable=False, index=True),
    sa.Column('json_data', sa.UnicodeText(1024)),

    # wwwpoll specific columns
    sa.Column(
        'created',
        sa.DateTime,
        default=sa.func.now(),
        nullable=False,
        index=True),
    sa.Column(
        'updated',
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
        nullable=False,
        index=True),
    sa.Column('read', sa.Boolean(), default=False),
    sa.Column('shown', sa.Boolean(), default=False),

    #    sa.UniqueConstraint('to_username','notify_type','json_data',name='yo_wwwpoll_idx'),
    mysql_engine='InnoDB',
)

# This is where ALL notifications go, not to be confused with the wwwpoll
# transport specific table above
notifications_table = sa.Table(
    'yo_notifications',
    metadata,
    sa.Column('nid', sa.String(36), primary_key=True),
    sa.Column('notify_type', sa.String(20), nullable=False, index=True),
    sa.Column('to_username', sa.String(20), nullable=False, index=True),
    sa.Column('from_username', sa.String(20), index=True, nullable=True),
    sa.Column('json_data', sa.UnicodeText(1024)),
    sa.Column(
        'created',
        sa.DateTime,
        default=sa.func.now(),
        nullable=False,
        index=True),
    sa.Column(
        'updated',
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
        nullable=False,
        index=True),

    # non-wwwpoll columns
    sa.Column('priority_level', sa.Integer, index=True, default=3),
    sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True),
    sa.Column('trx_id', sa.String(40), index=True, nullable=True),
    sa.UniqueConstraint(
        'to_username',
        'notify_type',
        'trx_id',
        'from_username',
        name='yo_notification_idx'),
    mysql_engine='InnoDB',
)

actions_table = sa.Table(
    'yo_actions',
    metadata,
    sa.Column('aid', sa.Integer, primary_key=True),
    sa.Column('nid', None, sa.ForeignKey('yo_notifications.nid')),
    sa.Column('transport', sa.String(20), nullable=False, index=True),
    sa.Column('status', sa.String(20), nullable=False, index=True),
    sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True),
    sa.UniqueConstraint('aid', 'nid', 'transport', name='yo_wwwpoll_idx'),
    mysql_engine='InnoDB',
)

user_settings_table = sa.Table(
    'yo_user_settings',
    metadata,
    sa.Column('username', sa.String(20), primary_key=True),
    sa.Column(
        'transports',
        sa.UnicodeText,
        index=False,
        default=DEFAULT_USER_TRANSPORT_SETTINGS_STRING,
        nullable=False),
    sa.Column('created', sa.DateTime, default=sa.func.now(), index=False),
    sa.Column(
        'updated',
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
        nullable=False,
        index=True),
    mysql_engine='InnoDB',
)


def is_duplicate_entry_error(error):
    if isinstance(error, (IntegrityError, SQLiteIntegrityError)):
        msg = str(error).lower()
        return "unique" in msg
    return False


class YoDatabase:
    def __init__(self, db_url=None):
        self.db_url = db_url
        self.engine = sa.create_engine(self.db_url)
        self.metadata = metadata
        self.metadata.create_all(bind=self.engine)
        self.url = make_url(self.db_url)

    @contextmanager
    def acquire_conn(self):
        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    @property
    def backend(self):
        return self.url.get_backend_name()

    def _get_notifications(self,
                           table=None,
                           nid=None,
                           to_username=None,
                           created_before=None,
                           updated_after=None,
                           read=None,
                           notify_types=None,
                           limit=30):
        """Returns an SQLAlchemy result proxy with the notifications stored in wwwpoll table matching the specified params

       Keyword args:
          nid(int):            notification id
          username(str):       the username to lookup notifications for
          created_before(str): ISO8601-formatted timestamp
          updated_after(str):  ISO8601-formatted
          read(bool):          if set, only return notifications where the read flag is set to this value
          notify_types(list):  if set, only return notifications of one of the types specified in this list
          limit(int):          return at most this number of notifications

       Returns:
          list
       """
        with self.acquire_conn() as conn:
            try:
                query = table.select()
                if nid:
                    return conn.execute(query.where(table.c.nid == nid))
                if to_username:
                    query = query.where(table.c.to_username == to_username)
                if created_before:
                    created_before_val = dateutil.parser.parse(created_before)
                    query = query.where(table.c.created >= created_before_val)
                if updated_after:
                    updated_after_val = dateutil.parser.parse(updated_after)
                    query = query.where(table.c.updated <= updated_after_val)
                if read:
                    query = query.where(table.c.read == read)
                if notify_types:
                    query = query.filter(table.c.notify_type.in_(notify_types))
                query = query.limit(limit)
                return conn.execute(query)
            except BaseException:
                logger.exception('_get_notifications failed')
        return []

    def get_notifications(self, **kwargs):
        kwargs['table'] = notifications_table
        return self._get_notifications(**kwargs)

    def get_wwwpoll_notifications(self, **kwargs):
        kwargs['table'] = wwwpoll_table
        return self._get_notifications(**kwargs)

    def _create_notification(self, table=None, **notification):
        with self.acquire_conn() as conn:
            tx = conn.begin()
            try:
                result = conn.execute(table.insert(), **notification)
                logger.debug('_create_notification response: %s', result)

                tx.commit()
                return True
            except (IntegrityError, SQLiteIntegrityError) as e:
                if is_duplicate_entry_error(e):
                    logger.debug(
                        '_create_notification ignoring duplicate entry error')
                    return True
                else:
                    logger.exception(
                        '_create_notification failed to add notification')
                    tx.rollback()
            except BaseException:
                tx.rollback()
                logger.exception(
                    '_create_notification failed for %s' % notification)
            return False

    def wwwpoll_mark_shown(self, nid):
        logger.debug('wwwpoll: marking %s as shown', nid)
        with self.acquire_conn() as conn:
            try:
                query = wwwpoll_table.update() \
                    .where(wwwpoll_table.c.nid == nid) \
                    .values(shown=True)
                conn.execute(query)
                return True
            except BaseException:
                logger.exception('wwwpoll_mark_shown failed')
        return False

    def wwwpoll_mark_unshown(self, nid):
        logger.debug('wwwpoll: marking %s as unshown', nid)
        with self.acquire_conn() as conn:
            try:
                query = wwwpoll_table.update() \
                    .where(wwwpoll_table.c.nid == nid) \
                    .values(shown=False)
                conn.execute(query)
                return True
            except BaseException:
                logger.exception('wwwpoll_mark_unshown failed')
        return False

    def wwwpoll_mark_read(self, nid):
        logger.debug('wwwpoll: marking %s as read', nid)
        with self.acquire_conn() as conn:
            try:
                query = wwwpoll_table.update() \
                    .where(wwwpoll_table.c.nid == nid) \
                    .values(read=True)
                conn.execute(query)
                return True
            except BaseException:
                logger.exception('wwwpoll_mark_read failed')
        return False

    def wwwpoll_mark_unread(self, nid):
        logger.debug('wwwpoll: marking %s as unread', nid)
        with self.acquire_conn() as conn:
            try:
                query = wwwpoll_table.update() \
                    .where(wwwpoll_table.c.nid == nid) \
                    .values(read=False)
                conn.execute(query)
                return True
            except BaseException:
                logger.exception('wwwpoll_mark_unread failed')
        return False

    def create_user(self, username, transports=None):
        if transports:
            transports = json.dumps(transports)
        else:
            transports = DEFAULT_USER_TRANSPORT_SETTINGS_STRING
        user_settings_data = {'username': username, 'transports': transports}
        with self.acquire_conn() as conn:
            try:
                stmt = user_settings_table.insert(values=user_settings_data)
                _ = conn.execute(stmt)
                return True
            except BaseException:
                logger.exception('create_user failed')
            return False

    def get_user_transports(self, username=None):
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
                if not (results is None):
                    json_settings = results['transports']
                    return json.loads(json_settings)
                else:
                    logger.info(
                        'get_user_transports no user found, creating new user')
                    self.create_user(username)
                    select_response = conn.execute(query)
                    results = select_response.fetchone()
                    json_settings = results['transports']
                    return json.loads(json_settings)
            except BaseException:
                logger.exception('get_user_transports failed')
            return False

    def set_user_transports(self, username=None, transports=None):
        """ Sets the JSON object representing user's configured transports
        This method does only basic sanity checks, it should only be invoked via the API server
        Args:
            username(str):    the user whose transports need to be set
            transports(dict): maps transports to dicts containing 'notification_types' and 'sub_data' keys
        """
        with self.acquire_conn() as conn:
            # user exists
            # user doesnt exist
            try:
                stmt = user_settings_table.update().where(
                    user_settings_table.c.username == username). \
                    values(transports=json.dumps(transports))
                result = conn.execute(stmt).first()
                logger.debug('set_user_transpors update result: %s', result)
                return transports
            except Exception as e:
                logger.exception(
                    'Exception occurred trying to update transports for user %s to %s'
                    % (username, str(transports)))
                result = self.create_user(username, transports=transports)
                logger.debug('set_user_transports insert result: %s', result)
                if result:
                    return transports
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
            except BaseException:
                logger.exception('Exception occurred!')
        return retval

    def create_wwwpoll_notification(self,
                                    notify_id=None,
                                    notify_type=None,
                                    created_time=None,
                                    raw_data={},
                                    to_username=None,
                                    shown=False,
                                    read=False):
        """ Creates a new notification in the wwwpoll table

        Keyword Args:
           notify_id(str):    if not provided, will be autogenerated as a UUID
           notify_type(str):  the notification type
           created_time(str): ISO8601-formatted timestamp, if not set current time will be used
           raw_data(dict):    what to include in the data field of the stored notification, will be JSON-serialised for storage
           to_user(str):      the username we're sending to
           shown(bool):       whether or not the notification should start marked as shown (default False)
           read(bool):       whether or not the notification should start marked as shown (default False)

        Returns:
           dict: the notification as stored in wwwpoll, None on error
        """

        if notify_id is None:
            notify_id = str(uuid.uuid4)
        if created_time is None:
            created_time = datetime.datetime.now()
        notification = {
            'nid': notify_id,
            'notify_type': notify_type,
            'created': created_time,
            'updated': created_time,
            'to_username': to_username,
            'shown': shown,
            'read': read
        }
        raw_data_json = json.dumps(raw_data)
        notification['json_data'] = raw_data
        with self.acquire_conn() as conn:
            success = False
            tx = conn.begin()
            try:
                insert_response = conn.execute(wwwpoll_table.insert(),
                                               **notification)
                tx.commit()
                return True
            except (IntegrityError, SQLiteIntegrityError) as e:
                if is_duplicate_entry_error(e):
                    logger.debug('Ignoring duplicate entry error')
                    return True
                else:
                    logger.exception('failed to add notification')
                    tx.rollback()
                    return False
            except BaseException:
                tx.rollback()
                logger.exception(
                    'Failed to create new wwwpoll notification object: %s' %
                    notification)
                return False

    def create_notification(self, **notification_object):
        """ Creates an unsent notification in the DB

        Keyword Args:
           notification_object(dict): the actual notification to create+store

        Returns:
          True on success, False on error
        """
        if not 'nid' in notification_object.keys():
            notification_object['nid'] = str(uuid.uuid4())
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
