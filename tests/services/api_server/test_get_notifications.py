# -*- coding: utf-8 -*-

from datetime import datetime

import pytest
import yo.json
from yo.services.api_server.api_methods import api_get_notifications


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
        'json_data':     yo.json.dumps(vote_data),
        'to_username': 'testuser1337',
        'from_username': 'testuser1336',
        'notify_type': 'vote',
        'trx_id': '123abc'
    }
    yo_db = sqlite_db
    retval = yo_db.create_notification(**test_data)
    assert retval is True

    result = await api_get_notifications(
        username='testuser1337', context=dict(yo_db=sqlite_db))

    assert len(result) == 1
    result = result[0]

    assert result['notify_type'] == 'vote'
    assert result['to_username'] == 'testuser1337'
    assert result['from_username'] == 'testuser1336'
    assert yo.json.loads(result['json_data']) == vote_data
    assert isinstance(result['created'], datetime)

    # notifications only columns
    assert result['trx_id'] == '123abc'


