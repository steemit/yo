# -*- coding: utf-8 -*-

import ujson
from collections.abc import MutableMapping
from typing import Optional
from typing import List

import sqlalchemy as sa
import structlog
from pylru import WriteThroughCacheManager
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert

from ..schema import NOTIFICATION_TYPES

from yo.db import metadata

class UserNotFoundError(Exception):
    pass

logger = structlog.getLogger(__name__, source='users')


DEFAULT_SENTINEL = 'default_transports'

DEFAULT_USER_TRANSPORT_SETTINGS = {
    "desktop": {
        "notification_types": NOTIFICATION_TYPES,
        "data": None
    }
}

DEFAULT_USER_TRANSPORT_SETTINGS_STRING = ujson.dumps(DEFAULT_USER_TRANSPORT_SETTINGS)


CREATE_USER_STMT = '''INSERT INTO users(username,transports, created, updated) VALUES($1,$2,NOW(),NOW()) ON CONFLICT DO NOTHING RETURNING username'''
CREATE_USER_WITHOUT_TRANSPORTS_STMT = '''INSERT INTO users(username) VALUES($1) ON CONFLICT DO NOTHING RETURNING username'''
UPDATE_USER_TRANSPORTS_STMT = '''UPDATE users SET transports = $1 WHERE username = $2 RETURNING username'''
GET_USER_TRANSPORTS_STMT = '''SELECT transports FROM users WHERE username = $1'''


user_settings_table = sa.Table(
    'users', metadata,
    sa.Column('username', sa.Text, primary_key=True),
    sa.Column(
        'transports',
        JSONB(),
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
    sa.Index('users_transports_ix', 'transports', postgresql_using='gin'))




class UserManager(MutableMapping):
    def __init__(self, engine):
        self.engine = engine

    def __get_default(self, transports=None):
        return dict(updated=sa.func.now(),
                    transports=transports or DEFAULT_USER_TRANSPORT_SETTINGS_STRING,
                    )

    def __getitem__(self, username):
        try:
            user_query = user_settings_table.select().where(
                user_settings_table.c.username == username)
            with self.engine.connect() as conn:
                select_response = conn.execute(user_query)
                user = select_response.first()
            if not user:
                raise KeyError
            return user
        except KeyError:
            self[username] = DEFAULT_SENTINEL
            return self[username]

    def __setitem__(self, username, transports):
        # Add the key/value pair to the cache and store.
        if transports == DEFAULT_SENTINEL:
            defaults = self.__get_default(username)
        else:
            defaults = self.__get_default(transports)

        upsert_stmt = insert(user_settings_table).\
            on_conflict_do_update(
                constraint=user_settings_table.primary_key,
                set_=defaults)
        with self.engine.connect() as conn:
            conn.execute(upsert_stmt, username=username)

    def __delitem__(self, key):
        raise NotImplementedError

    def __iter__(self):
        stmt = user_settings_table.select()
        with self.engine.connect() as conn:
            for row in conn.execute(stmt):
                yield (row.username,
                        dict(transports=row.transports,
                             created=row.created,
                             updated=row.updated))

    def __len__(self):
        stmt = user_settings_table.count()
        with self.engine.connect() as conn:
            return conn.scalar(stmt)

    def __contains__(self, username):
        with self.engine.connect() as conn:
            s = select([user_settings_table.c.username]).where(
                user_settings_table.c.username == username)
            return conn.execute(s).scalar() == username

    def keys(self):
        return tuple(r[0] for r in self)

    def values(self):
        return tuple(r[1] for r in self)

    def items(self):
        return tuple(r for r in self)

    def popitem(self):
        raise NotImplementedError

    def pop(self, key, default=None):
        raise NotImplementedError


# async user methods
async def create_user(conn, username:str, transports:Optional[dict]=None) -> bool:
    transports = transports or DEFAULT_USER_TRANSPORT_SETTINGS
    logger.info('creating user', username=username, transports=transports)

    try:
        new_username = await conn.fetchval(CREATE_USER_STMT,username,transports)
        logger.info('user created', username=username, created=new_username)
        return new_username

    except BaseException:
        logger.exception(
            'create_user failed',
            username=username,
            transports=transports,
            exc_info=True)
    return False


async def get_user_transports(conn, username:str=None) -> dict:
    """Returns the JSON object representing user's configured transports

   This method does no validation on the object, it is assumed that the object was validated in set_user_transports

   Args:
      username(str): the username to lookup

   Returns:
      dict: the transports configured for the user
   """

    try:
        user = await conn.fetchrow(GET_USER_TRANSPORTS_STMT,username)
        if not user:
            raise UserNotFoundError()
        return user['transports']
    except UserNotFoundError:
        result = await create_user(conn, username=username)
        if result:
            return DEFAULT_USER_TRANSPORT_SETTINGS
        raise ValueError('No user found or created')

    except BaseException as e:
        logger.exception('get_user_transports failed', username=username)
        raise e

async def set_user_transports(conn, username:str=None, transports:dict=None) -> bool:
    """ Sets the JSON object representing user's configured transports
    This method does only basic sanity checks, it should only be invoked via the API server
    Args:
        username(str):    the user whose transports need to be set
        transports(dict): maps transports to dicts containing 'notification_types' and 'sub_data' keys
    """

    try:

        result = await conn.execute(UPDATE_USER_TRANSPORTS_STMT, transports, username)
        if result > 0:
            return True
    except Exception as e:
        logger.error(
            'unable to update transports',
            e=e,
            username=username,
            transports=transports,
            )

    logger.info('creating user to set transports', username=username)
    return await create_user(conn, username, transports=transports) is not None


async def get_user_email(username:str=None) -> str:
    return 'email@domain.com'

async def get_user_phone(username:str=None) -> str:
    return '+15555555555'
