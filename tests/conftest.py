import json
import os

import pytest

import yo.mock_notifications
import yo.mock_settings
from yo.db_utils import init_db

no_docker = pytest.mark.skipif(
    os.getenv('INDOCKER', '0') == '1', reason='Does not work inside docker')
mysql_test = pytest.mark.skipif(
    os.getenv('SKIPMYSQL', '0') == '1', reason='Skipping MySQL tests')
source_code_path = os.path.dirname(os.path.realpath(__file__))

TESTUSER_TRANSPORTS = {
    'username': 'testuser1337',
    'transports': json.dumps(yo.mock_settings.YoMockSettings().create_defaults())
}


def add_test_users(sqlite_db):
    sqlite_db.create_user('test_user1')
    sqlite_db.create_user('test_user2')
    sqlite_db.create_user('testuser_3')

@pytest.fixture(scope='function')
def sqlite_db():
    """Returns a new instance of YoDatabase backed by sqlite3 memory with the mock data preloaded"""
    yo_db = init_db(db_url='sqlite://', reset=True)
    return yo_db

@pytest.fixture(scope='function')
def sqlite_db_with_data():
    yield init_db(db_url='sqlite://', reset=True)

@pytest.fixture
def fake_notifications():
    return [
        {
            'notify_type': 'reward',
            'to_username': 'test_user',
            'json_data': {
                'reward_type':'curation',
                'item': dict(
                    author='test_user',
                    category='test',
                    permlink='test-post',
                    summary='A test post'),
                'amount': dict(SBD=6.66, SP=13.37)
            },
        }
    ]
