# -*- coding: utf-8 -*-
import asyncio
from contextlib import contextmanager
import datetime
import enum
from enum import IntEnum
from sqlite3 import IntegrityError as SQLiteIntegrityError
from typing import NamedTuple
import uuid

from aiopg.sa import create_engine
import dateutil
import dateutil.parser
import sqlalchemy as sa
from sqlalchemy import Integer
from sqlalchemy import cast
from sqlalchemy import event
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import and_
import structlog
import toolz

import ujson

from .services.registration import Registration
from .services.registration import ServiceState

logger = structlog.getLogger(__name__, source='YoDatabase')

metadata = sa.MetaData()

NOTIFY_TYPES = ('power_down', 'power_up', 'resteem', 'feed', 'reward', 'send', 'mention',
                'follow', 'vote', 'comment_reply', 'post_reply', 'account_update',
                'message', 'receive')

TRANSPORT_TYPES = ('email', 'sms', 'wwwpoll')


class NotificationType(IntEnum):
    power_down = enum.auto()
    power_up = enum.auto()
    resteem = enum.auto()
    feed = enum.auto()
    reward = enum.auto()
    send = enum.auto()
    mention = enum.auto()
    follow = enum.auto()
    vote = enum.auto()
    comment_reply = enum.auto()
    post_reply = enum.auto()
    account_update = enum.auto()
    message = enum.auto()
    receive = enum.auto()


class TransportType(IntEnum):
    email = 1
    wwwpoll = 2
    sms = 3


class Priority(IntEnum):
    MARKETING = 1
    LOW = 2
    NORMAL = 3
    HIGH = 4
    ALWAYS = 5


class ActionStatus(IntEnum):
    SENT = 1
    RATE_LIMITED = 2
    OP_TYPE_MUTED = 3


class NotificationResult(NamedTuple):
    nid: str
    transport: TransportType
    status: ActionStatus


class UserNotFoundError(Exception):
    pass


DEFAULT_USER_TRANSPORT_SETTINGS = {
    "email": {
        "notification_types": [],
        "sub_data": {}
    },
    "wwwpoll": {
        "notification_types": [
            "power_down", "power_up", "resteem", "feed", "reward", "send", "mention",
            "follow", "vote", "comment_reply", "post_reply", "account_update", "message",
            "receive"
        ],
        "sub_data": {}
    }
}

DEFAULT_USER_TRANSPORT_SETTINGS_STRING = ujson.dumps(DEFAULT_USER_TRANSPORT_SETTINGS)

wwwpoll_table = sa.Table(
    'yo_wwwpoll',
    metadata,
    sa.Column('nid', sa.String(32), primary_key=True, default=lambda: uuid.uuid4().hex),
    sa.Column('notify_type', sa.String(20), nullable=False, index=True),
    sa.Column(
        'to_username',
        sa.String(20),
        sa.ForeignKey('yo_user_settings.username'),
        nullable=False,
        index=True),
    sa.Column('trx_id', sa.String(40), index=True, nullable=True),
    sa.Column(
        'from_username',
        sa.String(20),
        sa.ForeignKey('yo_user_settings.username'),
        nullable=True,
        index=True),
    sa.Column('json_data', sa.UnicodeText()),

    # wwwpoll specific columns
    sa.Column('created', sa.DateTime, default=sa.func.now(), nullable=False, index=True),
    sa.Column(
        'updated',
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
        index=True),
    sa.Column('read', sa.Boolean(), default=False),
    sa.Column('shown', sa.Boolean(), default=False),
)
wwwpoll_postgres_index = sa.Index(
    'ix_yo_wwwpoll_unique',
    'to_username',
    'notify_type',
    'trx_id',
    'from_username',
    text("md5(json_data)"),
    unique=True)
wwwpoll_generic_index = sa.Index(
    'ix_yo_wwwpoll_unique',
    'to_username',
    'notify_type',
    'trx_id',
    'from_username',
    'json_data',
    unique=True)

notifications_table = sa.Table(
    'yo_notifications',
    metadata,
    sa.Column('nid', sa.String(32), primary_key=True, default=lambda: uuid.uuid4().hex),
    sa.Column('notify_type', sa.String(20), nullable=False, index=True),
    sa.Column(
        'to_username',
        sa.String(20),
        sa.ForeignKey('yo_user_settings.username'),
        nullable=False,
        index=True),
    sa.Column('trx_id', sa.String(40), index=True, nullable=True),
    sa.Column(
        'from_username',
        sa.String(20),
        sa.ForeignKey('yo_user_settings.username'),
        index=True,
        nullable=True),
    sa.Column('json_data', sa.UnicodeText()),
    sa.Column('created', sa.DateTime, default=sa.func.now(), nullable=False, index=True),
    sa.Column(
        'updated',
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
        index=True),

    # non-wwwpoll columns
    sa.Column('sent', sa.Boolean, index=True, nullable=False, default=False),
    sa.Column('priority_level', sa.Integer, index=True, default=3),
    sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True),
)

notifications_postgres_index = sa.Index(
    'ix_yo_notifications_unique',
    'to_username',
    'notify_type',
    'trx_id',
    'from_username',
    text("md5(json_data)"),
    unique=True)
notifications_generic_index = sa.Index(
    'ix_yo_notifications_unique',
    'to_username',
    'notify_type',
    'trx_id',
    'from_username',
    'json_data',
    unique=True)

actions_table = sa.Table('yo_actions', metadata,
                         sa.Column('aid', sa.Integer, primary_key=True),
                         sa.Column('nid',
                                   sa.String(32), sa.ForeignKey('yo_notifications.nid')),
                         sa.Column('transport', sa.Integer, nullable=False, index=True),
                         sa.Column('status', sa.Integer, nullable=False, index=True),
                         sa.Column(
                             'created_at', sa.DateTime, default=sa.func.now(),
                             index=True),
                         sa.UniqueConstraint('nid', 'transport', name='yo_actions_ix'))

user_settings_table = sa.Table(
    'yo_user_settings', metadata,
    sa.Column('username', sa.String(20), primary_key=True),
    sa.Column(
        'transports',
        JSONB().with_variant(sa.UnicodeText(), dialect_name='sqlite'),
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
        index=True), sa.Index('yo_transports_ix', 'transports', postgresql_using='gin'))

services_table = sa.Table('yo_services', metadata,
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
                          sa.Index(
                              'only_one_enabled_service',
                              'service_name',
                              'service_status',
                              unique=True,
                              postgresql_where=sa.Column('service_status') == 1))


# pylint: disable=unused-argument
@event.listens_for(notifications_table, 'before_create')
def receive_before_create(target, connection, **kwargs):
    if connection.engine.dialect.name == 'postgresql':
        if target == notifications_table:
            target.append_constraint(notifications_postgres_index)
        elif target == wwwpoll_table:
            target.append_constraint(wwwpoll_postgres_index)
    else:
        if target == notifications_table:
            target.append_constraint(notifications_generic_index)
        elif target == wwwpoll_table:
            target.append_constraint(wwwpoll_generic_index)


# pylint: enable=unused-argument


def is_duplicate_entry_error(error):
    if isinstance(error, (IntegrityError, SQLiteIntegrityError)):
        msg = str(error).lower()
        return "unique" in msg
    return False


# pylint: disable-msg=no-value-for-parameter,too-many-public-methods,protected-access
class YoDatabase:
    def __init__(self, db_url=None):
        self.db_url = db_url
        self.url = make_url(self.db_url)
        if self.backend == 'postgres':
            self.loop = asyncio.get_event_loop()
            self.async_engine = self.loop.run_until_complete(
                create_engine(
                    user=self.url.username,
                    password=self.url.password,
                    host=self.url.host,
                    port=self.url.port,
                    database=self.url.database))
            self.engine = sa.create_engine(self.db_url)
        else:
            self.engine = sa.create_engine(self.db_url)
        self.metadata = metadata
        self.metadata.create_all(bind=self.engine)

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
                        '__create_generic_notification ignoring duplicate entry error')
                    return True
                else:
                    logger.exception('__create_generic_notification failed',
                                     **notification)
                    tx.rollback()
                    return False
            except BaseException:
                tx.rollback()
                logger.exception('__create_generic_notification failed', **notification)

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
        results = []

        # make sure all usernames exists before creating notifications
        usernames = [notification['to_username']]
        if notification.get('from_username'):
            usernames.append(notification['from_username'])
        results.append(self.create_users(usernames))

        results.append(self.create_db_notification(**notification))
        results.append(self.create_wwwpoll_notification(**notification))
        return all(results)

    async def create_notifications(self, notifications):
        results = []

        # create non-existant users before creating notifications
        usernames = []
        for notification in notifications:
            usernames.append(notification['to_username'])
            usernames.append(notification.get('from_username'))
        usernames = set(u for u in usernames if u)

        results.append(await self.create_users(usernames))

        # group notifications by keys to allow multi-row inserts
        # grouped_notifications = toolz.groupby(lambda x: tuple(x.keys()),
        #                                      notifications)
        # logger.debug('create_notifications',
        #             notification_count=len(notifications),
        #             group_count=len(grouped_notifications.keys()))
        #futures = []

        wwwpoll_columns = set(c.name for c in wwwpoll_table.c._all_columns)
        async with self.async_engine.acquire() as conn:
            for n in notifications:
                results.append(await
                               conn.execute(notifications_table.insert().values(**n)))
                n2 = toolz.keyfilter(lambda k: k in wwwpoll_columns, n)
                results.append(await conn.execute(wwwpoll_table.insert().values(**n2)))
        return all(results)

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
                resp = conn.execute(query).fetchall()

                return list(map(dict, resp))

            except BaseException as e:
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
                    limit=30,
                    e=e,
                    exc_info=True)
        return []
        # pylint: enable=too-many-arguments,too-many-locals

    def get_db_notifications(self, **kwargs):
        kwargs['table'] = notifications_table
        return self.__get_notifications(**kwargs)

    def get_wwwpoll_notifications(self, **kwargs):
        kwargs['table'] = wwwpoll_table
        return self.__get_notifications(**kwargs)

    def get_db_unsents(self):
        # pylint: disable=singleton-comparison
        with self.acquire_conn() as conn:
            users_join = notifications_table.join(
                user_settings_table,
                notifications_table.c.to_username == user_settings_table.c.username)
            unsent_query = select([notifications_table,
                                   user_settings_table.c.transports]).\
                select_from(users_join).where(notifications_table.c.sent == False).\
                limit(5000)
            result = conn.execute(unsent_query).fetchall()
        unsents = list(map(dict, result))
        for u in unsents:
            u['transports'] = ujson.loads(u['transports'])
        return unsents
        # pylint: enable=singleton-comparison

    def get_wwwpoll_unsents(self):
        return self.get_wwwpoll_notifications(shown=False)

    # notification sent/shown/read methods
    def mark_db_notification_sent(self, nid):
        return self.__mark_notification(notifications_table, nid, 'sent', True)

    def mark_db_notifications_sent(self, nids):
        logger.debug('mark_db_notifications_sent', nids=len(nids))
        with self.acquire_conn() as conn:
            try:
                # pylint: disable=no-value-for-parameter
                stmt = notifications_table.update().where(
                    notifications_table.c.nid.in_(nids)).values(sent=True)
                # pylint: enable=no-value-for-parameter
                conn.execute(stmt)
                return True
            except BaseException:
                logger.exception('mark_db_notification_sent failed', nids=len(nids))
        return False

    def __mark_notification(self, tbl, nid, name, value):
        logger.debug('__mark_notification', tbl=tbl, name=name, nid=nid, value=value)
        with self.acquire_conn() as conn:
            try:
                # pylint: disable=no-value-for-parameter
                query = tbl.update().where(tbl.c.nid == nid).values(**{name: value})
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

    # user methods
    def create_user(self, username, transports=None):
        logger.info('creating user', username=username, transports=transports)

        user_settings_data = {'username': username}
        if transports:
            if isinstance(transports, dict):
                transports = ujson.dumps(transports)
            user_settings_data.update({'transports': transports})

        with self.acquire_conn() as conn:
            try:
                stmt = user_settings_table.insert(values=user_settings_data)
                result = conn.execute(stmt)
                if result.inserted_primary_key:
                    logger.info('user created', username=username)
                    return True
            except (IntegrityError, SQLiteIntegrityError) as e:
                if is_duplicate_entry_error(e):
                    logger.debug('create_user ignoring duplicate entry error')
                    return True
                else:
                    logger.exception(
                        'create_user failed',
                        username=username,
                        transports=transports,
                        exc_info=True)
                    return False
            except BaseException:
                logger.exception(
                    'create_user failed',
                    username=username,
                    transports=transports,
                    exc_info=True)
        return False

    async def create_users(self, usernames):
        usernames = list(set(usernames))
        logger.debug('creating users', username_count=len(usernames))
        if not usernames:
            return True

        if self.backend == 'postgres':
            create_stmt = insert(user_settings_table). \
                on_conflict_do_nothing(index_elements=['username'])
        else:
            create_stmt = user_settings_table.insert(). \
                prefix_with('OR IGNORE')

        results = []
        async with self.async_engine.acquire() as conn:
            for username in usernames:
                try:
                    results.append(await conn.execute(
                        create_stmt.values(username=username)))
                except BaseException:
                    logger.exception(
                        'create_users failed', usernames=usernames, exc_info=True)
                    results.append(False)
        return results

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
                logger.exception('get_user_transports failed', username=username)
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

    def get_users_rates(self, usernames):
        # pylint: disable=too-many-locals
        with self.acquire_conn() as conn:

            notifications_join = actions_table.join(
                notifications_table, actions_table.c.nid == notifications_table.c.nid)
            rates_query = \
                select([notifications_table.c.to_username,
                        sa.func.count().label('total'),
                        sa.func.sum(
                            cast(
                                actions_table.c.created_at < sa.func.now() - datetime.timedelta(
                                    hours=24), Integer)
                        ).label('day_total'),
                        sa.func.sum(
                            cast(
                                actions_table.c.created_at < sa.func.now() - datetime.timedelta(
                                    hours=1), Integer
                            )
                        ).label('hour_total')]) \
                .select_from(notifications_join). \
                where(and_(
                    actions_table.c.status == int(ActionStatus.SENT),
                    notifications_table.c.to_username.in_(usernames))). \
                group_by(notifications_table.c.to_username)
            rates = conn.execute(rates_query).fetchall()
        return rates

    # actions methods
    def create_action(self, notification, transport, status=None):
        with self.acquire_conn() as conn:
            create_action_stmt = actions_table.insert().values(
                nid=notification['nid'], transport=transport, status=status)
            result = conn.execute(create_action_stmt)
            return result.inserted_primary_key

    def store_notification_results(self, transport, sent, failed, muted, rate_limited):
        logger.debug(
            'store_notification_results',
            transport=transport,
            sent_count=len(sent),
            failed_count=len(failed),
            muted_count=len(muted),
            rate_limited_count=len(rate_limited))
        actions = []
        if sent:
            actions.extend(
                dict(
                    nid=n['nid'],
                    transport=int(TransportType[transport]),
                    status=int(ActionStatus.SENT)) for n in sent)
        if rate_limited:
            actions.extend(
                dict(
                    nid=n['nid'],
                    transport=int(TransportType[transport]),
                    status=int(ActionStatus.RATE_LIMITED)) for n in rate_limited)
        if not actions:
            return True

        handled_nids = [a['nid'] for a in actions]
        with self.acquire_conn() as conn:
            logger.debug(
                'store_notification_results inserting', actions_count=len(actions))
            try:
                conn.execute(actions_table.insert(), actions)
            except IntegrityError:
                logger.info('insert actions individually to avoid duplicate error')
                good_actions = []
                for action in actions:
                    try:
                        conn.execute(actions_table.insert().values(**action))
                    except IntegrityError:
                        logger.info('ignoring action integrity error', action=action)
                    good_actions.append(action)
                handled_nids = [a['nid'] for a in good_actions]

            except Exception as e:
                logger.exception('failed to store notification results', e=e)
                return False
        logger.debug('marking notifications as sent', count=len(handled_nids))
        self.mark_db_notifications_sent(handled_nids)

    # service methods
    # pylint: disable=no-self-use
    def register_service(self, conn, service_name):
        logger.info('registering service', service_name=service_name)
        tbl = services_table

        # add service to services table
        create_service_tx = conn.begin()
        create_service_stmt = tbl.insert().values(service_name=service_name)
        result = conn.execute(create_service_stmt)
        service_id = result.inserted_primary_key[0]
        create_service_tx.commit()

        result = Registration(
            service_name=service_name,
            service_id=service_id,
            service_status=ServiceState.DISABLED,
            service_extra={})
        logger.info('service registered', registration=result)
        return result
    # pylint: enable=no-self-use

    def unregister_service(self, registration):
        logger.info('unregistering service', registration=registration)
        tbl = services_table
        with self.acquire_conn() as conn:
            delete_service_tx = conn.begin()
            # remove service from services table
            delete_service_stmt = tbl.delete().\
                where(tbl.c.service_id == registration.service_id)
            _ = conn.execute(delete_service_stmt)
            delete_service_tx.commit()
            logger.debug(
                'service unregistered',
                service_name=registration.service_name,
                service_id=registration.service_id)

    # pylint: disable=too-many-locals
    def heartbeat(self, registration: Registration):
        tbl = services_table
        service_name = registration.service_name
        service_id = registration.service_id
        log = logger.bind(service_id=service_id, service_name=service_name)
        log.info('heartbeat received')

        with self.acquire_conn() as conn:
            # prune stale services
            self.prune_stale_services(conn)

        with self.acquire_conn() as conn:
            # prune stale services
            self.prune_stale_services(conn)

            # lock services of same type
            adjust_enabled_services_tx = conn.begin()
            lock_services_stmt = tbl.select().with_for_update(). \
                where(tbl.c.service_name == service_name)
            services = conn.execute(lock_services_stmt).fetchall()
            existing_service_ids = set(s['service_id'] for s in services)

            # service not stored in table
            if not service_id or service_id not in existing_service_ids:
                # assign id
                registration = self.register_service(conn, registration.service_name)
                service_name = registration.service_name
                service_id = registration.service_id
                log = logger.bind(service_id=service_id, service_name=service_name)

            # adjust enabled services
            enabled_services_count = sum(s['service_status'] for s in services)
            log.debug('enabled services count', count=enabled_services_count)

            # enable service if it is the only one registered
            if enabled_services_count != 1:
                log.info('enabled services count != 1', count=enabled_services_count)
                self.disable_services(conn, service_name)
                log.info('enabling service')
                self.enable_service(conn, service_id)
            else:
                log.debug('updating heartbeat datetime')
                self.update_service(conn, service_id)

            adjust_enabled_services_tx.commit()

        # read state from new transaction and return it to service
        with self.acquire_conn() as conn:
            # read service status from db and return it to service
            registration = self.get_service(conn, service_id)
            log.debug('registration result', registration=registration)
            return registration

    # pylint: disable=no-self-use
    def enable_service(self, conn, service_id):
        tbl = services_table
        update_status_stmt = tbl.update().where(tbl.c.service_id == service_id).values(
            service_status=int(ServiceState.ENABLED))
        result = conn.execute(update_status_stmt)
        logger.debug('enable service', rowcount=result.rowcount)
        assert result.rowcount == 1

    def update_service(self, conn, service_id):
        tbl = services_table
        update_heartbeat_timestamp_stmt = tbl.update(). \
            where(tbl.c.service_id == service_id). \
            values(updated=sa.func.now())
        result = conn.execute(update_heartbeat_timestamp_stmt)
        assert result.rowcount == 1

    def disable_services(self, conn, service_name):
        tbl = services_table
        logger.info('disabling all instances of service type', type=service_name)
        reset_all_services_stmt = tbl.update(). \
            where(tbl.c.service_name == service_name). \
            values(service_status=int(ServiceState.DISABLED))
        result = conn.execute(reset_all_services_stmt)
        logger.debug('disable all services', rowcount=result.rowcount)

    def prune_stale_services(self, conn):
        tbl = services_table
        prune_tx = conn.begin()
        prune_stale_services_stmt = tbl.delete(). \
            where(tbl.c.updated < (
                sa.func.now() - datetime.timedelta(seconds=25)))
        result = conn.execute(prune_stale_services_stmt)
        logger.debug('pruned stale services', pruned_count=result.rowcount)
        prune_tx.commit()

    def get_service(self, conn, service_id):
        tbl = services_table
        query = tbl.select().where(tbl.c.service_id == service_id)
        row = conn.execute(query).first()
        return Registration(
            service_name=row['service_name'],
            service_id=row['service_id'],
            service_status=row['service_status'],
            service_extra=row['service_extra'])
