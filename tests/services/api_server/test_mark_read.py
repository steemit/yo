# -*- coding: utf-8 -*-

from datetime import datetime

import pytest
import yo.json
from yo.services.api_server.api_methods import api_mark_read



@pytest.mark.asyncio
async def test_api_mark_read(sqlite_db):
    test_notification = {
        'json_data':     yo.json.dumps({
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
    result = await api_mark_read(ids=[notification['nid']], context=dict(yo_db=sqlite_db))
    assert result == [True]
    notification = sqlite_db.get_wwwpoll_notifications()[0]
    assert notification['read'] is True
