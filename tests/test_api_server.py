import pytest

from yo import api_server


@pytest.mark.asyncio
async def test_api_get_notifications(sqlite_db_with_data):
    """Basic test of get_notifications with mocked_notifications.py stuff"""
    API = api_server.YoAPIServer()
    API.testing_allowed = True
    some_notifications = await API.api_get_notifications(
        username='test_user', test=True, limit=5)
    assert len(some_notifications) == 5


@pytest.mark.asyncio
async def test_api_get_notifications_sqlite(sqlite_db_with_data):
    """Basic test of get_notifications backed by sqlite3"""
    API = api_server.YoAPIServer()
    API.testing_allowed = False  # we only want real DB data

    some_notifications = await API.api_get_notifications(
        username='test_user', limit=5, yo_db=sqlite_db_with_data)
    assert len(some_notifications) == 5





@pytest.mark.asyncio
async def test_api_get_set_transports_sqlite(sqlite_db):
    """Test get and set transports backed by MySQL with simple non-default transports"""
    API = api_server.YoAPIServer()
    API.testing_allowed = False  # we only want real DB data
    simple_transports_obj = {
        'email': {
            'notification_types': ['vote', 'comment'],
            'sub_data': 'testuser1337@example.com'
        },
        'wwwpoll': {
            'notification_types': ['mention', 'post_reply'],
            'sub_data': {
                'stuff': 'not here by default'
            }
        }
    }

    resp = await API.api_set_transports(
        username='testuser1337',
        transports=simple_transports_obj,
        test=False,
        yo_db=sqlite_db)
    assert resp == simple_transports_obj

    resp = await API.api_get_transports(
        username='testuser1337', test=False, yo_db=sqlite_db)
    assert resp == simple_transports_obj
