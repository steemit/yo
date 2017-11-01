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
        'notify_type':                             'vote',
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
            'notify_type':           'vote',
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
            'notify_type':           'vote',
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
            'notify_type':           'vote',
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
            'notify_type':           'vote',
            'priority_level': 1
        },

    ]

    API = api_server.YoAPIServer()

    for notification in notifications:
        sqlite_db.create_notification(**notification)

    some_notifications = await API.api_get_notifications(
        to_username='test_user1337',context=dict(yo_db=sqlite_db))
    assert len(some_notifications) == 5



@pytest.mark.asyncio
async def test_api_get_set_transports_sqlite(sqlite_db):
    """Test get and set transports backed by sqlite with simple non-default transports"""
    API = api_server.YoAPIServer()

    simple_transports_obj = {
        'username':'testuser1337',
        'transports': {
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
    }

    sqlite_db.create_user('testuser1337')
    resp = await API.api_set_transports(
        username='testuser1337',
        transports=simple_transports_obj['transports'],
        context=dict(yo_db=sqlite_db))
    assert resp == simple_transports_obj['transports']

    resp = await API.api_get_transports(
        username='testuser1337', context=dict(yo_db=sqlite_db))
    assert resp == simple_transports_obj['transports']
