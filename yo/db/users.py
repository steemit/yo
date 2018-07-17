# -*- coding: utf-8 -*-
import asyncio
import ujson
from collections.abc import MutableMapping
from collections import namedtuple
from typing import Optional
from typing import TypeVar

import sqlalchemy as sa
import structlog

from asyncpg.pool import Pool
from asyncpg.connection import Connection

from pylru import WriteThroughCacheManager
from sqlalchemy.dialects.postgresql import JSONB

from yo.rpc_client import get_user_data

from ..schema import NOTIFICATION_TYPES
from ..schema import NotificationType

from yo.db import metadata

class UserNotFoundError(Exception):
    pass

logger = structlog.getLogger(__name__, source='users')

PoolOrConn = TypeVar('PoolOrConn', Pool, Connection)

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


async def create_user(conn:PoolOrConn, username:str, transports:dict=None) -> bool:
    transports = transports or DEFAULT_USER_TRANSPORT_SETTINGS
    logger.debug('creating user', username=username, transports=transports)
    try:
        new_username = await conn.fetchval(CREATE_USER_STMT,username,transports)
        if new_username is None:
            return False
        logger.debug('user created', username=username, created=new_username)
        return True
    except BaseException:
        logger.exception(
            'create_user failed',
            username=username,
            transports=transports,
            exc_info=True)
    return False

async def get_user_transports(conn:PoolOrConn, username:str) -> dict:
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

async def set_user_transports(conn:PoolOrConn, username:str, transports:dict=None) -> bool:
    try:
        result = await conn.fetchval(UPDATE_USER_TRANSPORTS_STMT, transports, username)
        if result:
            return True
    except Exception as e:
        logger.error(
            'unable to update transports',
            e=e,
            username=username,
            transports=transports,
            )

    logger.info('creating user to set transports', username=username)
    return await create_user(conn, username, transports=transports)

async def get_user_email(username:str=None) -> str:
    response = await get_user_data(username)
    return response['email']

async def get_user_phone(username:str=None) -> str:
    response = await get_user_data(username)
    return response['phone']


async def get_user_transports_for_notification(conn:PoolOrConn, username:str, notification_type:NotificationType) -> list:
    transports = await get_user_transports(conn, username)
    name = notification_type.name
    return [k for k,v in transports.items() if name in v['notification_types']]


class User:
    def __init__(self,username, transports):
        self.username = username
        self.transports = transports

    def transports_for(self, event_type):
        return [k for k, v in self.transports.items() if event_type in v['notification_types']]

    def email(self):
        pass

    def phone(self):
        pass

def _run(coro, loop=None):
    loop = loop or asyncio.get_event_loop()
    return loop.run_until_complete(coro)

class Users(MutableMapping):
    def __init__(self, pool:Pool):
        self.pool = pool

    def __getitem__(self, username:str):
        return _run(get_user_transports(self.pool, username))

    def __setitem__(self, username, transports):
        _run(set_user_transports(self.pool, username))

    def __delitem__(self, key):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def __contains__(self, username):
        raise NotImplementedError

    def keys(self):
        raise NotImplementedError

    def values(self):
        raise NotImplementedError

    def items(self):
        raise NotImplementedError

    def popitem(self):
        raise NotImplementedError

    def pop(self, key, default=None):
        raise NotImplementedError


async def create_users_writethrough_cache_async(pool):
    users = Users(pool)
    return WriteThroughCacheManager(users, 100000)


def create_users_writethrough_cache(pool):
    return _run(create_users_writethrough_cache_async(pool))


