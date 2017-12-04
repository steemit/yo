# -*- coding: utf-8 -*-
from contextlib import contextmanager
import datetime
from enum import IntFlag
from sqlite3 import IntegrityError as SQLiteIntegrityError
import uuid

import dateutil
import dateutil.parser
import sqlalchemy as sa
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import IntegrityError
import structlog

import ujson

from .services.registration import Registration
from .services.registration import ServiceState

logger = structlog.getLogger(__name__, source='YoDatabase')

metadata = sa.MetaData()

NOTIFY_TYPES = ('power_down', 'power_up', 'resteem', 'feed', 'reward', 'send',
                'mention', 'follow', 'vote', 'comment_reply', 'post_reply',
                'account_update', 'message', 'receive')

TRANSPORT_TYPES = ('email', 'sms', 'wwwpoll')


class Priority(IntFlag):
    MARKETING = 1
    LOW = 2
    NORMAL = 3
    PRIORITY = 4
    ALWAYS = 5


class UserNotFoundError(Exception):
    pass


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

DEFAULT_USER_TRANSPORT_SETTINGS_STRING = ujson.dumps(
    DEFAULT_USER_TRANSPORT_SETTINGS)

# This is the table queried by API server for the wwwpoll transport
wwwpoll_table = sa.Table(
    'yo_wwwpoll',
    metadata,
    sa.Column(
        'nid',
        sa.String(32),
        primary_key=True,
        default=lambda: uuid.uuid4().hex),
    sa.Column('notify_type', sa.String(20), nullable=False, index=True),
    sa.Column('to_username', sa.String(20), nullable=False, index=True),
    sa.Column('from_username', sa.String(20), nullable=True, index=True),
    sa.Column('json_data', sa.UnicodeText()),

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
        onupdate=sa.func.now(),
        nullable=False,
        index=True),
    sa.Column('read', sa.Boolean(), default=False),
    sa.Column('shown', sa.Boolean(), default=False),
    # sa.UniqueConstraint('to_username','notify_type','json_data',name='yo_wwwpoll_idx')
)

# This is where ALL notifications go, not to be confused with the wwwpoll
# transport specific table above
notifications_table = sa.Table(
    'yo_notifications',
    metadata,
    sa.Column(
        'nid',
        sa.String(32),
        primary_key=True,
        default=lambda: uuid.uuid4().hex),
    sa.Column('notify_type', sa.String(20), nullable=False, index=True),
    sa.Column('to_username', sa.String(20), nullable=False, index=True),
    sa.Column('from_username', sa.String(20), index=True, nullable=True),
    sa.Column('json_data', sa.UnicodeText()),
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
        onupdate=sa.func.now(),
        nullable=False,
        index=True),

    # non-wwwpoll columns
    sa.Column('sent', sa.Boolean, index=True, default=False),
    sa.Column('priority_level', sa.Integer, index=True, default=3),
    sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True),
    sa.Column('trx_id', sa.String(40), index=True, nullable=True),
    sa.UniqueConstraint(
        'to_username',
        'notify_type',
        'trx_id',
        'from_username',
        'json_data',
        name='yo_notification_idx'))

actions_table = sa.Table(
    'yo_actions', metadata,
    sa.Column('aid', sa.Integer, primary_key=True),
    sa.Column('nid', None, sa.ForeignKey('yo_notifications.nid')),
    sa.Column('transport', sa.String(20), nullable=False, index=True),
    sa.Column('status', sa.String(20), nullable=False, index=True),
    sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True),
    sa.UniqueConstraint('aid', 'nid', 'transport', name='yo_wwwpoll_idx'))

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
        onupdate=sa.func.now(),
        nullable=False,
        index=True),
)

services_table = sa.Table(
    'yo_services',
    metadata,
    sa.Column('service_id', sa.Integer, primary_key=True),
    sa.Column('service_name', sa.String(30), nullable=False),
    sa.Column(
        'service_status',
        sa.Integer,
        default=int(ServiceState.DISABLED),
        nullable=False),
    sa.Column('service_extra', sa.String(300)),
    sa.Column(
        'updated',
        sa.DateTime,
        nullable=False,
        default=sa.func.now(),
        onupdate=sa.func.now()),
)


def is_duplicate_entry_error(error):
    if isinstance(error, (IntegrityError, SQLiteIntegrityError)):
        msg = str(error).lower()
        return "unique" in msg
    return False


# pylint: disable-msg=no-value-for-parameter,too-many-public-methods
class YoDatabase:
    def __init__(self, db_url=None):
        self.db_url = db_url
        self.engine = sa.create_engine(self.db_url)
        self.metadata = metadata
        self.metadata.create_all(bind=self.engine)
        self.url = make_url(self.db_url)

        self.clear_services()

    # db helper methods
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

    # create notification methods
    def __create_generic_notification(self, table=None, **notification):
        with self.acquire_conn() as conn:
            tx = conn.begin()
            try:
                result = conn.execute(table.insert(), **notification)

                tx.commit()
                logger.debug(
                    'notification_stored',
                    nid=result.inserted_primary_key,
                    notify_type=notification.get('notify_type)'))
                return True
            except (IntegrityError, SQLiteIntegrityError) as e:
                if is_duplicate_entry_error(e):
                    logger.debug(
                        '__create_generic_notification ignoring duplicate entry error'
                    )
                    return True
                else:
                    logger.exception('__create_generic_notification failed',
                                     **notification)
                    tx.rollback()
                    return False
            except BaseException:
                tx.rollback()
                logger.exception('__create_generic_notification failed',
                                 **notification)

            return False

    def create_db_notification(self, **notification):
        """ Creates a new notification in the notifications table

        Returns:
            bool:             True on success, False otherwise
        """
        table = notifications_table
        return self.__create_generic_notification(table=table, **notification)

    def create_wwwpoll_notification(self, **notification):
        """ Creates a new notification in wwwpoll table

        Returns:
            bool:             True on success, False otherwise
        """
        table = wwwpoll_table
        return self.__create_generic_notification(table=table, **notification)

    def create_notification(self, **notification):
        return all([
            self.create_db_notification(**notification),
            self.create_wwwpoll_notification(**notification)
        ])

    # notification retrieval methods

    # pylint: disable=too-many-arguments,too-many-locals
    def __get_notifications(self,
                            table=None,
                            nid=None,
                            to_username=None,
                            created_before=None,
                            updated_after=None,
                            read=None,
                            shown=False,
                            sent=False,
                            notify_types=None,
                            priority=None,
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
                if shown:
                    query = query.where(table.c.shown == shown)
                if sent:
                    query = query.where(table.c.sent == sent)
                if notify_types:
                    query = query.filter(table.c.notify_type.in_(notify_types))
                if priority:
                    query = query.filter(table.c.priority_level >= priority)
                query = query.limit(limit)
                resp = conn.execute(query)
                if resp is not None:
                    return list(map(dict, resp.fetchall()))

            except BaseException:
                logger.exception(
                    '__get_notifications failed',
                    table=table,
                    nid=nid,
                    to_username=to_username,
                    created_before=created_before,
                    updated_after=updated_after,
                    read=read,
                    shown=shown,
                    sent=sent,
                    notify_types=notify_types,
                    priority=priority,
                    limit=30)
        return []
        # pylint: enable=too-many-arguments,too-many-locals

    def get_db_notifications(self, **kwargs):
        kwargs['table'] = notifications_table
        return self.__get_notifications(**kwargs)

    def get_wwwpoll_notifications(self, **kwargs):
        kwargs['table'] = wwwpoll_table
        return self.__get_notifications(**kwargs)

    def get_db_unsents(self):
        return self.get_db_notifications(sent=False)

    def get_wwwpoll_unsents(self):
        return self.get_wwwpoll_notifications(shown=False)

    # notification sent/shown/read methods
    def mark_db_notification_sent(self, nid):
        return self.__mark_notification(notifications_table, nid, 'sent', True)

    def mark_db_notifications_sent(self, nids):
        logger.debug('mark_db_notifications_sent', nids=nids)
        with self.acquire_conn() as conn:
            try:
                # pylint: disable=no-value-for-parameter
                stmt = notifications_table.update().where(
                    notifications_table.c.nid in nids).values(sent=True)
                # pylint: enable=no-value-for-parameter
                conn.execute(stmt)
                return True
            except BaseException:
                logger.exception('mark_db_notification_sent failed', nids=nids)
        return False

    def __mark_notification(self, tbl, nid, name, value):
        logger.debug(
            '__mark_notification', tbl=tbl, name=name, nid=nid, value=value)
        with self.acquire_conn() as conn:
            try:
                # pylint: disable=no-value-for-parameter
                query = tbl.update().where(tbl.c.nid == nid).values(
                    **{
                        name: value
                    })
                # pylint: enable=no-value-for-parameter
                conn.execute(query)
                return True
            except BaseException:
                logger.exception(
                    '__mark_notification failed',
                    tbl=tbl,
                    name=name,
                    nid=nid,
                    value=value)
        return False

    def wwwpoll_mark_shown(self, nid):
        return self.__mark_notification(wwwpoll_table, nid, 'shown', True)

    def wwwpoll_mark_unshown(self, nid):
        return self.__mark_notification(wwwpoll_table, nid, 'shown', False)

    def wwwpoll_mark_read(self, nid):
        return self.__mark_notification(wwwpoll_table, nid, 'read', True)

    def wwwpoll_mark_unread(self, nid):
        return self.__mark_notification(wwwpoll_table, nid, 'read', False)

    # notification priorty query method
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
                query = query.where(notifications_table.c.sent)
                query = query.where(
                    notifications_table.c.sent_at >= start_time)
                select_response = conn.execute(query)
                retval = select_response.rowcount
            except BaseException:
                logger.exception('Exception occurred!')
        return retval

    # user methods
    def create_user(self, username, transports=None):
        logger.info('creating user', username=username, transports=transports)

        transports = transports or DEFAULT_USER_TRANSPORT_SETTINGS
        user_settings_data = {
            'username': username,
            'transports': ujson.dumps(transports)
        }

        with self.acquire_conn() as conn:
            try:
                stmt = user_settings_table.insert(values=user_settings_data)
                result = conn.execute(stmt)
                if result.inserted_primary_key:
                    logger.info('user created', username=username)
                    return True
            except BaseException:
                logger.exception(
                    'create_user failed',
                    username=username,
                    transports=transports,
                    exc_info=True)
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
                user_query = user_settings_table.select().where(
                    user_settings_table.c.username == username)
                select_response = conn.execute(user_query)
                user = select_response.first()
                if not user:
                    raise UserNotFoundError()
                return ujson.loads(user['transports'])

            except UserNotFoundError:
                result = self.create_user(username=username)
                if result:
                    return DEFAULT_USER_TRANSPORT_SETTINGS
                raise ValueError('No user found or created')

            except BaseException as e:
                logger.exception(
                    'get_user_transports failed', username=username)
                raise e

    def set_user_transports(self, username=None, transports=None):
        """ Sets the JSON object representing user's configured transports
        This method does only basic sanity checks, it should only be invoked via the API server
        Args:
            username(str):    the user whose transports need to be set
            transports(dict): maps transports to dicts containing 'notification_types' and 'sub_data' keys
        """
        with self.acquire_conn() as conn:
            try:
                set_transpors_stmt = user_settings_table.update().\
                    where(user_settings_table.c.username == username).\
                    values(transports=ujson.dumps(transports))
                result = conn.execute(set_transpors_stmt)
                if result.rowcount > 0:
                    return True
            except sa.exc.SQLAlchemyError:
                logger.info(
                    'unable to update transports',
                    username=username,
                    transports=transports)

            logger.info('creating user to set transports', username=username)
            if self.create_user(username, transports=transports):
                return True
            return False

    # service methods
    def register_service(self, service_name):
        logger.info('registering service', service_name=service_name)
        tbl = services_table
        with self.acquire_conn() as conn:
            create_service_tx = conn.begin()
            # add service to services table
            create_service_stmt = tbl.insert().values(
                service_name=service_name)
            result = conn.execute(create_service_stmt)
            service_id = result.inserted_primary_key[0]
            logger.debug(
                'service registered',
                service_name=service_name,
                service_id=service_id)
            create_service_tx.commit()

            # adjust number of enabled services
            adjust_enabled_services_tx = conn.begin()
            lock_services_stmt = tbl.select().with_for_update(). \
                where(tbl.c.service_name == service_name)
            conn.execute(lock_services_stmt)
            enabled_services_query = tbl.count().where(
                tbl.c.service_name == service_name).\
                where(tbl.c.service_status == int(ServiceState.ENABLED))
            enabled_services = conn.scalar(enabled_services_query)
            logger.debug(
                'enabled services count',
                service_name=service_name,
                count=enabled_services)

            # enable service if it is the only one registered
            if enabled_services < 1:
                logger.debug('enabling service', service_name=service_name)
                update_status_stmt = tbl.update().where(
                    tbl.c.service_id == service_id).values(
                        service_status=int(ServiceState.ENABLED))
                conn.execute(update_status_stmt)
            adjust_enabled_services_tx.commit()

            # read service status from db and return it to service
            query = tbl.select().where(tbl.c.service_id == service_id)
            row = conn.execute(query).first()
            result = Registration(
                service_name=row['service_name'],
                service_id=row['service_id'],
                service_status=row['service_status'],
                service_extra=row['service_extra'])

            logger.debug('registration result', registration=result)
            return result

    def unregister_service(self, registration):
        logger.info('unregistering service', registration=registration)
        tbl = services_table
        with self.acquire_conn() as conn:
            disable_service_tx = conn.begin()
            # remove service from services table
            disable_service_stmt = tbl.delete().\
                where(tbl.c.service_id == registration.service_id)
            _ = conn.execute(disable_service_stmt)
            disable_service_tx.commit()
            logger.debug(
                'service unregistered',
                service_name=registration.service_name,
                service_id=registration.service_id)

    def heartbeat(self, registration: Registration):
        logger.info('heartbeat received', **registration.asdict())
        tbl = services_table
        service_name = registration.service_name
        service_id = registration.service_id
        with self.acquire_conn() as conn:
            # adjust number of enabled services
            adjust_enabled_services_tx = conn.begin()
            lock_services_stmt = tbl.select().with_for_update().\
                where(tbl.c.service_name == service_name)
            conn.execute(lock_services_stmt)
            enabled_services_query = tbl.count().where(
                tbl.c.service_name == service_name). \
                where(tbl.c.service_status == int(ServiceState.ENABLED))
            enabled_services = conn.scalar(enabled_services_query)
            logger.debug(
                'enabled services count',
                service_name=service_name,
                count=enabled_services)

            # enable service if it is the only one registered
            if enabled_services < 1:
                logger.debug('enabling %s service', service_name)
                update_status_stmt = tbl.update().where(
                    tbl.c.service_id == service_id).values(
                        service_status=int(ServiceState.ENABLED))
                conn.execute(update_status_stmt)
            adjust_enabled_services_tx.commit()

            # read service status from db and return it to service
            query = tbl.select().where(
                tbl.c.service_id == registration.service_id)
            row = conn.execute(query).first()
            result = Registration(
                service_name=row['service_name'],
                service_id=row['service_id'],
                service_status=row['service_status'],
                service_extra=row['service_extra'])
            logger.debug('registration result', registration=result)
            return result

    def clear_services(self):
        logger.info('resetting services table')
        tbl = services_table
        with self.acquire_conn() as conn:
            conn.execute(tbl.delete())
