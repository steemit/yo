# -*- coding: utf-8 -*-
from datetime import datetime
import json

import pytest

import yo.api_methods


@pytest.mark.asyncio
async def test_api_get_notifications(sqlite_db):
    """Basic test of get_db_notifications backed by sqlite3"""
    vote_data = {
        'author': 'testuser1337',
        'weight': 100,
        'item': {
            'author': 'testuser1337',
            'permlink': 'test-post-1',
            'summary': 'A test post',
            'category': 'test',
            'depth': 0
        }
    }
    test_data = {
        'json_data': json.dumps(vote_data),
        'to_username': 'testuser1337',
        'from_username': 'testuser1336',
        'notify_type': 'vote',
        'trx_id': '123abc'
    }
    yo_db = sqlite_db
    retval = yo_db.create_notification(**test_data)
    assert retval is True

    result = await yo.api_methods.api_get_notifications(
        username='testuser1337', context=dict(yo_db=sqlite_db))

    assert len(result) == 1
    result = result[0]

    assert result['notify_type'] == 'vote'
    assert result['to_username'] == 'testuser1337'
    assert result['from_username'] == 'testuser1336'
    assert json.loads(result['json_data']) == vote_data
    assert isinstance(result['created'], datetime)

    # notifications only columns
    assert result['trx_id'] == '123abc'


@pytest.mark.asyncio
async def test_api_mark_read(sqlite_db):
    test_notification = {
        'json_data': json.dumps({
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
        'to_username': 'testuser1337',
        'from_username': 'testuser1336',
        'notify_type': 'vote',
    }
    _ = sqlite_db.create_wwwpoll_notification(**test_notification)
    assert _ is True
    notification = sqlite_db.get_wwwpoll_notifications()[0]
    assert notification['read'] is False
    result = await yo.api_methods.api_mark_read(ids=[notification['nid']], context=dict(yo_db=sqlite_db))
    assert result == [True]
    notification = sqlite_db.get_wwwpoll_notifications()[0]
    assert notification['read'] is True


@pytest.mark.asyncio
async def test_api_mark_unread(sqlite_db):
    test_notification = {
        'json_data': json.dumps({
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
        'to_username': 'testuser1337',
        'from_username': 'testuser1336',
        'notify_type': 'vote',
        'read': True
    }

    _ = sqlite_db.create_wwwpoll_notification(**test_notification)
    assert _ is True
    notification = sqlite_db.get_wwwpoll_notifications()[0]
    assert notification['read'] is True
    result = await yo.api_methods.api_mark_unread(ids=[notification['nid']],
                                       context=dict(yo_db=sqlite_db))
    assert result == [True]
    notification = sqlite_db.get_wwwpoll_notifications()[0]
    assert notification['read'] is False


@pytest.mark.asyncio
async def test_api_mark_shown(sqlite_db):
    test_notification = {
        'json_data': json.dumps({
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
        'to_username': 'testuser1337',
        'from_username': 'testuser1336',
        'notify_type': 'vote',
    }

    _ = sqlite_db.create_wwwpoll_notification(**test_notification)
    assert _ is True
    notification = sqlite_db.get_wwwpoll_notifications()[0]
    assert notification['shown'] is False
    result = await yo.api_methods.api_mark_shown(ids=[notification['nid']],
                                      context=dict(yo_db=sqlite_db))
    assert result == [True]
    notification = sqlite_db.get_wwwpoll_notifications()[0]
    assert notification['shown'] is True


@pytest.mark.asyncio
async def test_api_mark_unshown(sqlite_db):
    test_notification = {
        'json_data': json.dumps({
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
        'to_username': 'testuser1337',
        'from_username': 'testuser1336',
        'notify_type': 'vote',
        'shown': True
    }

    _ = sqlite_db.create_wwwpoll_notification(**test_notification)
    assert _ is True
    notification = sqlite_db.get_wwwpoll_notifications()[0]
    assert notification['shown'] is True
    result = await yo.api_methods.api_mark_unshown(ids=[notification['nid']],
                                        context=dict(yo_db=sqlite_db))
    assert result == [True]
    notification = sqlite_db.get_wwwpoll_notifications()[0]
    assert notification['shown'] is False


@pytest.mark.asyncio
async def test_api_get_set_transports(sqlite_db):
    """Test get and set transports backed by sqlite with simple non-default transports"""


    simple_transports_obj = {
        'username': 'testuser1337',
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

    resp = await yo.api_methods.api_set_transports(
        username='testuser1337',
        transports=simple_transports_obj['transports'],
        context=dict(yo_db=sqlite_db))
    assert resp

    resp = await yo.api_methods.api_get_transports(
        username='testuser1337', context=dict(yo_db=sqlite_db))
    assert resp == simple_transports_obj['transports']
