from yo import db
import json
import os

import pytest
from sqlalchemy import MetaData

from yo import db
from yo import mock_notifications
from yo import mock_settings
from yo.db_utils import init_db





def test_empty_sqlite():
    """Test we can get a simple empty sqlite database"""
    yo_db = db.YoDatabase(db_url='sqlite://')
    assert len(yo_db.engine.table_names()) == 0

def test_schema_sqlite():
    """Test init_schema creates empty tables"""
    yo_db = init_db(db_url='sqlite://', reset=True)
    m = MetaData()
    m.create_all(bind=yo_db.engine)
    for table in m.tables.values():
        with yo_db.acquire_conn() as conn:
            query = table.select().where(True)
            response = conn.execute(query).fetchall()
            assert len(response) == 0

def test_wwwpoll_notification():
    """Test making a wwwpoll notification and retrieving it"""
    db_url='sqlite://'
    vote_data = {
        'author': 'testuser1336',
        'weight': 100,
        'item': {
            'author': 'testuser1337',
            'permlink': 'test-post-1',
            'summary': 'A test post',
            'category': 'test',
            'depth': 0
        }
    }
    test_initdata = [('notifications', {
        'trx_id': 1337,
        'json_data': json.dumps(vote_data),
        'to_username': 'testuser1337',
        'from_username': 'testuser1336',
        'type': 'vote',
        'priority_level': db.PRIORITY_LEVELS['low']
    })]

    yo_db = init_db(db_url=db_url, reset=True)
    retval = yo_db.create_wwwpoll_notification(
        notify_type='vote', to_user='testuser1337', raw_data=vote_data)
    assert retval is not None
    assert 'notify_id' in retval.keys()
    assert retval['notify_type'] == 'vote'
    assert retval['username'] == 'testuser1337'

    new_notify_id = retval['notify_id']
    get_resp = yo_db.get_wwwpoll_notifications(
        username='testuser1337', limit=2).fetchall()
    assert len(get_resp) == 1
    assert get_resp[0]['notify_id'] == new_notify_id
    assert get_resp[0]['read'] == False
    assert get_resp[0]['seen'] == False
    assert get_resp[0]['username'] == 'testuser1337'
    assert json.loads(get_resp[0]['data']) == vote_data
