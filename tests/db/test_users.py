# -*- coding: utf-8 -*-
import pytest

from yo.db.users import create_user
from yo.db.users import CREATE_USER_STMT
from yo.db.users import DEFAULT_USER_TRANSPORT_SETTINGS
from yo.db.users import get_user_transports
from yo.db.users import GET_USER_TRANSPORTS_STMT
from yo.db.users import set_user_transports
from yo.db.users import UPDATE_USER_TRANSPORTS_STMT

from yo.db.users import get_user_email
from yo.db.users import get_user_phone

TEST_USER_OBJECT = {
  "username": "test_username",
  "transports": {
    "desktop": {
      "data": None,
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
      ]
    }
  },
  "created": "2018-07-11 02:00:13.505257",
  "updated": "2018-07-11 02:00:13.505257"
}


@pytest.mark.asyncio
async def test_create_user(mocked_pool):
    mocked_pool.fetchval.return_value = 'test_username'
    result = await create_user(mocked_pool, 'test_username')
    assert result is True
    mocked_pool.fetchval.assert_called_once_with(CREATE_USER_STMT,
                                                 'test_username',
                                                 DEFAULT_USER_TRANSPORT_SETTINGS)

@pytest.mark.asyncio
async def test_get_user_transports_user_exists(mocked_pool):
    mocked_pool.fetchrow.return_value = TEST_USER_OBJECT
    result = await get_user_transports(mocked_pool, 'test_username')
    assert result == DEFAULT_USER_TRANSPORT_SETTINGS
    mocked_pool.fetchrow.assert_called_once_with(GET_USER_TRANSPORTS_STMT,
                                                 'test_username')


@pytest.mark.asyncio
async def test_get_user_transports_user_doesnt_exists(mocked_pool):
    mocked_pool.fetchrow.return_value = None
    result = await get_user_transports(mocked_pool, 'test_username')
    assert result == DEFAULT_USER_TRANSPORT_SETTINGS
    mocked_pool.fetchrow.assert_called_once_with(GET_USER_TRANSPORTS_STMT,
                                                 'test_username')
    mocked_pool.fetchval.assert_called_once_with(CREATE_USER_STMT,
                                                 'test_username',
                                                 DEFAULT_USER_TRANSPORT_SETTINGS)

@pytest.mark.asyncio
async def test_set_user_transports_user_exists(mocked_pool):
    mocked_pool.fetchval.return_value = 'test_username'
    result = await set_user_transports(mocked_pool,'test_username', DEFAULT_USER_TRANSPORT_SETTINGS)
    assert result is True
    mocked_pool.fetchval.assert_called_once_with(UPDATE_USER_TRANSPORTS_STMT,
                                                DEFAULT_USER_TRANSPORT_SETTINGS,
                                                'test_username')


@pytest.mark.asyncio
async def test_set_user_transports_user_doesnt_exist(mocked_pool):
    mocked_pool.fetchval.side_effect = [None,'test_username']
    result = await set_user_transports(mocked_pool,'test_username', DEFAULT_USER_TRANSPORT_SETTINGS)
    assert result is True
    mocked_pool.fetchval.assert_called_with(CREATE_USER_STMT,
                                            'test_username',
                                            DEFAULT_USER_TRANSPORT_SETTINGS)

    mocked_pool.fetchval.assert_any_call(UPDATE_USER_TRANSPORTS_STMT,
                                                DEFAULT_USER_TRANSPORT_SETTINGS,
                                                'test_username')


@pytest.mark.asyncio
async def test_get_user_email(mocked_pool):
    pass

@pytest.mark.asyncio
async def test_get_user_phone(mocked_pool):
    pass
