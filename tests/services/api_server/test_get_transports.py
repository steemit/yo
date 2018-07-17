# -*- coding: utf-8 -*-

from datetime import datetime

import pytest
import yo.json
from yo.services.api_server.api_methods import api_get_transports


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



    resp = await api_get_transports(
        username='testuser1337', context=dict(yo_db=sqlite_db))
    assert resp == simple_transports_obj['transports']
