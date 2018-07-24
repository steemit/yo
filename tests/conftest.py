# -*- coding: utf-8 -*-
import argparse
import logging
import os

import aiohttp
import asyncpg
import asyncpg.connection
import asyncpg.pool
import asyncpg.transaction

import asynctest

import pytest

def create_mocked_transaction():
    mocked_transaction = asynctest.create_autospec(
        asyncpg.transaction.Transaction)
    mocked_transaction.__await__ = asynctest.CoroutineMock()
    mocked_transaction.__aenter__ = asynctest.CoroutineMock()
    mocked_transaction.__aexit__ = asynctest.CoroutineMock()
    mocked_transaction.start = asynctest.CoroutineMock()
    mocked_transaction.commit = asynctest.CoroutineMock()
    mocked_transaction.rollback = asynctest.CoroutineMock()
    return mocked_transaction

def create_mocked_connection():
    mocked_transaction = create_mocked_transaction()
    mocked_conn = asynctest.create_autospec(asyncpg.connection.Connection)
    mocked_conn.transaction = asynctest.Mock(return_value=mocked_transaction)
    mocked_conn.fetchval = asynctest.CoroutineMock()
    mocked_conn.fetchrow = asynctest.CoroutineMock()
    mocked_conn.fetch = asynctest.CoroutineMock()
    mocked_conn.execute = asynctest.CoroutineMock()
    return mocked_conn

def create_mocked_pool():
    mocked_connection = create_mocked_connection()
    mocked_pool_acquire_context = asynctest.create_autospec(asyncpg.pool.PoolAcquireContext)
    mocked_pool_acquire_context.__aenter__ = asynctest.CoroutineMock(return_value=mocked_connection)
    mocked_pool_acquire_context.__await__ = asynctest.CoroutineMock(return_value=mocked_connection)

    mocked_pool = asynctest.create_autospec(asyncpg.pool.Pool)
    mocked_pool.acquire = asynctest.Mock(return_value=mocked_pool_acquire_context)
    mocked_pool.fetchval = asynctest.CoroutineMock()
    mocked_pool.fetchrow = asynctest.CoroutineMock()
    mocked_pool.fetch  = asynctest.CoroutineMock()
    mocked_pool.execute = asynctest.CoroutineMock()

    return mocked_pool


def create_mocked_aiohttp_client_response():
    response = asynctest.create_autospec(
        aiohttp.client_reqrep.ClientResponse)
    response.json = asynctest.CoroutineMock()
    return response


def create_mocked_aiohttp_client_request_context_manager():
    response = create_mocked_aiohttp_client_response()
    request_context_manager = asynctest.create_autospec(
        aiohttp.client._RequestContextManager)
    request_context_manager.__aenter__.return_value = response
    return request_context_manager


def create_mocked_aiohttp_client_session():
    request_context_manager = create_mocked_aiohttp_client_request_context_manager()
    mocked_client_session = asynctest.create_autospec(
    aiohttp.client.ClientSession)
    mocked_client_session.return_value = mocked_client_session
    mocked_client_session.__aenter__.return_value = mocked_client_session
    mocked_client_session.post.return_value = request_context_manager
    return mocked_client_session



@pytest.fixture(scope='function')
def mocked_pool():
    return create_mocked_pool()

@pytest.fixture
def mocked_conn():
    return create_mocked_connection()


@pytest.fixture
def mocked_rpc_client_session():
    return create_mocked_aiohttp_client_session()


@pytest.fixture
def fake_notifications():
    return [
        {
            'notify_type': 'reward',
            'to_username': 'test_user',
            'json_data': {
                'reward_type': 'curation',
                'item': dict(
                    author='test_user',
                    category='test',
                    permlink='test-post',
                    summary='A test post'),
                'amount': dict(SBD=6.66, SP=13.37)
            },
        }
    ]
