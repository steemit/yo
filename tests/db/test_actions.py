# -*- coding: utf-8 -*-
import pytest

from yo.schema import ActionStatus
from yo.schema import TransportType
import yo.db.actions
from yo.db.actions import store
from yo.db.actions import get_notification_state
from yo.db.actions import mark_failed
from yo.db.actions import mark_rate_limited
from yo.db.actions import mark_sent
from yo.db.actions import get_rates

@pytest.mark.asyncio
async def test_store(mocked_pool):
    mocked_pool.fetchval.return_value = 1
    result = await store(mocked_pool,
                         123,
                         'test_username',
                         TransportType.email,
                         ActionStatus.sent)
    assert result == 1
    mocked_pool.fetchval.assert_called_once_with(yo.db.actions.INSERT_ACTION_STMT,
                                                 123, # nid
                                                 'test_username', # username
                                                 TransportType.email, # transport
                                                 ActionStatus.sent # status
                                                 )

@pytest.mark.asyncio
async def test_get_notifications(mocked_pool):
    mocked_pool.fetchrow.return_value = 1
    result = await get_notification_state(mocked_pool, 1)
    assert result == 1
    mocked_pool.fetchrow.assert_called_once_with(yo.db.actions.GET_NOTIFICATION_STATE_STMT,
                                                 1 # nid
                                                 )

@pytest.mark.asyncio
async def test_fail(mocked_pool):
    mocked_pool.fetchrow.return_value = 1, 1, 1
    result = await mark_failed(mocked_pool, 1, TransportType.email)
    assert result == (1,1,1)
    mocked_pool.fetchrow.assert_called_once_with(yo.db.actions.FAIL_ACTION_STMT,
                                                 1, # nid
                                                 TransportType.email,
                                                 ActionStatus.failed,
                                                 yo.db.actions.PERMANENT_FAIL_COUNT,
                                                 ActionStatus.perm_failed
                                                 )

@pytest.mark.asyncio
async def test_rate_limited(mocked_pool):
    mocked_pool.fetchval.return_value = 1
    result = await mark_rate_limited(mocked_pool, 123, 'test_username', TransportType.email)
    assert result == 1
    mocked_pool.fetchval.assert_called_once_with(yo.db.actions.INSERT_ACTION_STMT,
        123,  # nid
        'test_username',  # username
        TransportType.email,  # transport
        ActionStatus.rate_limited  # status
        )

@pytest.mark.asyncio
async def test_sent(mocked_pool):
    mocked_pool.fetchval.return_value = 1
    result = await mark_sent(mocked_pool, 123, 'test_username', TransportType.email)
    assert result == 1
    mocked_pool.fetchval.assert_called_once_with(
        yo.db.actions.INSERT_ACTION_STMT,
        123,  # nid
        'test_username',  # username
        TransportType.email,  # transport
        ActionStatus.sent  # status
        )

@pytest.mark.asyncio
async def test_get_rates(mocked_pool):
    # FIXME
    pass
