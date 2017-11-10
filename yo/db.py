# coding=utf-8
import datetime
import json
import logging
import enum
import uuid
from contextlib import contextmanager

import dateutil
import dateutil.parser
import sqlalchemy as sa
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import IntegrityError
from sqlite3 import IntegrityError as SQLiteIntegrityError

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
    "email":   {
        "notification_types": [],
        "sub_data":           {}
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
        "sub_data":           {}
    }
}

DEFAULT_USER_TRANSPORT_SETTINGS_STRING = json.dumps(
    DEFAULT_USER_TRANSPORT_SETTINGS)

# This is the table queried by API server for the wwwpoll transport
wwwpoll_table = sa.Table(
        'yo_wwwpoll',
        metadata,
        sa.Column('nid', sa.String(32), primary_key=True,
                  default=lambda: uuid.uuid4().hex),
        sa.Column('notify_type', sa.String(20), nullable=False, index=True),
        sa.Column('to_username', sa.String(20), nullable=False, index=True),
        sa.Column('from_username', sa.String(20), index=True, nullable=True),
        sa.Column('json_data', sa.UnicodeText),
        sa.Column('created', sa.DateTime, default=sa.func.now(), nullable=False,
                  index=True),

        # wwwpoll specific columns
        sa.Column('updated', sa.DateTime, nullable=True, index=True,
                  onupdate=sa.func.now()),
        sa.Column('read', sa.Boolean, default=False),
        sa.Column('shown', sa.Boolean, default=False),

        sa.UniqueConstraint('to_username', 'notify_type', 'json_data',
                            name='ix_yo_wwwpoll_unique'),
        mysql_engine='InnoDB',
)

# This is where ALL notifications go, not to be confused with the wwwpoll transport specific table above
notifications_table = sa.Table(
        'yo_notifications',
        metadata,
        sa.Column('nid', sa.String(32), primary_key=True,
                  default=lambda: uuid.uuid4().hex),
        sa.Column('notify_type', sa.String(20), nullable=False, index=True),
        sa.Column('to_username', sa.String(20), nullable=False, index=True),
        sa.Column('from_username', sa.String(20), index=True, nullable=True),
        sa.Column('json_data', sa.UnicodeText),
        sa.Column('created', sa.DateTime, default=sa.func.now(), nullable=False,
                  index=True),

        # non-wwwpoll columns
        sa.Column('trx_id', sa.String(40), index=True, nullable=True),
        sa.UniqueConstraint('to_username', 'notify_type', 'trx_id',
                            'from_username', 'json_data',
                            name='ix_yo_notification_unique'),
        mysql_engine='InnoDB',
)

actions_table = sa.Table(
        'yo_actions',
        metadata,
        sa.Column('aid', sa.BigInteger().with_variant(sa.Integer, "sqlite"),
                  primary_key=True),
        sa.Column('nid', sa.String(32), nullable=False, index=True),
        sa.Column('transport', sa.String(20), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, index=True),
        sa.Column('created', sa.DateTime, default=sa.func.now(), index=True),
        sa.UniqueConstraint('aid', 'nid', 'transport',
                            name='ix_yo_actions_unique'),
        mysql_engine='InnoDB',
)

user_settings_table = sa.Table(
        'yo_user_settings',
        metadata,
        sa.Column('username', sa.String(20), primary_key=True),
        sa.Column('transports', sa.UnicodeText, index=False,
                  default=DEFAULT_USER_TRANSPORT_SETTINGS_STRING,
                  nullable=False),
        sa.Column('created', sa.DateTime, default=sa.func.now(), index=False),
        sa.Column('updated', sa.DateTime, default=sa.func.now(), index=False,
                  onupdate=sa.func.now()),
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
                    query = query.where(
                            table.c.created >= created_before_val)
                if updated_after:
                    updated_after_val = dateutil.parser.parse(updated_after)
                    query = query.where(
                            table.c.updated <= updated_after_val)
                if read:
                    query = query.where(table.c.read == read)
                if notify_types:
                    query = query.filter(
                            table.c.notify_type.in_(notify_types))
                query = query.limit(limit)
                return conn.execute(query)
            except:
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
                result = conn.execute(table.insert(),
                                      **notification)
                logger.debug('_create_notification response: %s',
                             result)

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
            except:
                tx.rollback()
                logger.exception(
                        '_create_notification failed for %s' % notification)
            return False

    def create_wwwpoll_notification(self,
                                    **notification):
        """ Creates a new notification in wwwpoll table

        Keyword Args:
            nid(int):
            notify_type(str):
            to_username(str):
            from_username(str):
            json_data(str):
            created(datetime):
            updated(datetime):
            read(bool):
            shown(bool):

        Returns:
            bool:             True on success, False otherwise
        """
        table = wwwpoll_table
        return self._create_notification(table=table, **notification)

    def create_notification(self, **notification):
        """ Creates a new notification in the notifications table

        Keyword Args:
            nid(int):
            notify_type(str):
            to_username(str):
            from_username(str):
            json_data(str):
            created(datetime):
            priority_level(int):
            trx_id(str):

        Returns:
            bool:             True on success, False otherwise
        """
        table = notifications_table
        return self._create_notification(table=table, **notification)

    def wwwpoll_mark_shown(self, nid):
        logger.debug('wwwpoll: marking %s as shown', nid)
        with self.acquire_conn() as conn:
            try:
                query = wwwpoll_table.update() \
                    .where(wwwpoll_table.c.nid == nid) \
                    .values(shown=True)
                conn.execute(query)
                return True
            except:
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
            except:
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
            except:
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
            except:
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
            except:
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
                results = select_response.first()
                if results:
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
            except:
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
                        'Exception occurred trying to update transports for user %s to %s' % (
                            username, str(transports)))
                result = self.create_user(username, transports=transports)
                logger.debug('set_user_transpors insert result: %s', result)
                if result:
                    return transports
            return False
