import time
import hashlib
import docker
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


def gen_initdata():
    """Utility function that generates some initdata using mock_notifications and mock_settings
       The returned initdata will fill the wwwpoll and user_settings table, but not the notifications table
       Default settings are used, with username@example.com as the email address
       This is sufficient for most testing purposes and also doubles as a partial test of the mock API
    """
    retval = []
    usernames = set()
    mock_data = yo.mock_notifications.YoMockData()
    for notification in mock_data.get_notifications(limit=9999):
        notification['data'] = json.dumps(notification['data'])
        retval.append(('wwwpoll', notification))
        usernames.add(notification['username'])
    mock_data = yo.mock_settings.YoMockSettings()
    retval.append(('user_settings', {
        'username': 'testuser1337',
        'transports': json.dumps(TESTUSER_TRANSPORTS)
    }))
    for user in usernames:
        user_transports_data = mock_data.get_transports(user)
        user_transports_data['email']['sub_data'] = '%s@example.com' % user
        user_transports_data = mock_data.set_transports(
            user, user_transports_data)
        retval.append(('user_settings', {
            'username': user,
            'transports': json.dumps(mock_data.get_transports(user))
        }))
    return retval



@pytest.fixture(scope='function')
def sqlite_db():
    """Returns a new instance of YoDatabase backed by sqlite3 memory with the mock data preloaded"""
    yo_db = init_db(db_url='sqlite://', reset=True)
    return yo_db

@pytest.fixture(scope='function')
def sqlite_db_with_data():
    yo_db = init_db(db_url='sqlite://', init_data=gen_initdata(), reset=True)
    return yo_db