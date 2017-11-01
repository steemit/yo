import pytest
import json
from yo import api_server




@pytest.mark.asyncio
async def test_api_get_notifications_sqlite(sqlite_db):
    """Basic test of get_notifications backed by sqlite3"""
    notifications = [
        {
        'trx_id':                           1337,
        'json_data':                        json.dumps({
            'author': 'testuser1336',
            'weight': 100,
            'item': {
                'author': 'testuser1337',
                'permlink': 'test-post-1',
                'summary': 'A test post',
                'category': 'test1',
                'depth': 0
            }
        }),
        'to_username':                      'testuser1337',
        'from_username':                    'testuser1336',
        'type':                             'vote',
        'priority_level': 1
        },
        {
            'trx_id':         1338,
            'json_data':      json.dumps({
                'author': 'testuser1336',
                'weight': 100,
                'item':   {
                    'author':   'testuser1337',
                    'permlink': 'test-post-1',
                    'summary':  'A test post',
                    'category': 'test2',
                    'depth':    0
                }
            }),
            'to_username':    'testuser1337',
            'from_username':  'testuser1336',
            'type':           'vote',
            'priority_level': 1
        },
        {
            'trx_id':         1338,
            'json_data':      json.dumps({
                'author': 'testuser1336',
                'weight': 100,
                'item':   {
                    'author':   'testuser1337',
                    'permlink': 'test-post-1',
                    'summary':  'A test post',
                    'category': 'test3',
                    'depth':    0
                }
            }),
            'to_username':    'testuser1337',
            'from_username':  'testuser1336',
            'type':           'vote',
            'priority_level': 1
        },
        {
            'trx_id':         1338,
            'json_data':      json.dumps({
                'author': 'testuser1336',
                'weight': 100,
                'item':   {
                    'author':   'testuser1337',
                    'permlink': 'test-post-1',
                    'summary':  'A test post',
                    'category': 'test4',
                    'depth':    0
                }
            }),
            'to_username':    'testuser1337',
            'from_username':  'testuser1336',
            'type':           'vote',
            'priority_level': 1
        },
        {
            'trx_id':         1338,
            'json_data':      json.dumps({
                'author': 'testuser1336',
                'weight': 100,
                'item':   {
                    'author':   'testuser1337',
                    'permlink': 'test-post-1',
                    'summary':  'A test post',
                    'category': 'test5',
                    'depth':    0
                }
            }),
            'to_username':    'testuser1337',
            'from_username':  'testuser1336',
            'type':           'vote',
            'priority_level': 1
        },

    ]

    API = api_server.YoAPIServer()


    for notification in notifications:
        sqlite_db.create_notification(**notification)
    some_notifications = await API.api_get_notifications(
        username='test_user', limit=5, yo_db=sqlite_db)
    assert len(some_notifications) == 5





@pytest.mark.asyncio
async def test_api_get_set_transports_sqlite(sqlite_db):
    """Test get and set transports backed by sqlite with simple non-default transports"""
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
        yo_db=sqlite_db)
    assert resp == simple_transports_obj

    resp = await API.api_get_transports(
        username='testuser1337', test=False, yo_db=sqlite_db)
    assert resp == simple_transports_obj
