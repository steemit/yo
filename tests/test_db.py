from yo import config
from yo import db
from yo import mock_notifications
from yo import mock_settings
from unittest import mock
from sqlalchemy import select
from sqlalchemy import MetaData
from sqlalchemy import func

import os
import pytest

from .conftest import MySQLServer
import socket
import time
import json

no_docker = pytest.mark.skipif(
    os.getenv('INDOCKER', '0') == '1', reason='Does not work inside docker')
mysql_test = pytest.mark.skipif(
    os.getenv('SKIPMYSQL', '0') == '1', reason='Skipping MySQL tests')
source_code_path = os.path.dirname(os.path.realpath(__file__))

TESTUSER_TRANSPORTS = {
    'username': 'testuser1337',
    'transports': json.dumps(mock_settings.YoMockSettings().create_defaults())
}


def gen_initdata():
    """Utility function that generates some initdata using mock_notifications and mock_settings
       The returned initdata will fill the wwwpoll and user_settings table, but not the notifications table
       Default settings are used, with username@example.com as the email address
       This is sufficient for most testing purposes and also doubles as a partial test of the mock API
    """
    retval = []
    usernames = set()
    mock_data = mock_notifications.YoMockData()
    for notification in mock_data.get_notifications(limit=9999):
        notification['data'] = json.dumps(notification['data'])
        retval.append(('wwwpoll', notification))
        usernames.add(notification['username'])
    mock_data = mock_settings.YoMockSettings()
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


@mysql_test
@no_docker
def test_run_mysql():
    """Test starting a MySQL server - this is sort of a metatest as the docker trick is used for other tests"""
    server = MySQLServer()
    server.stop()


def test_empty_sqlite():
    """Test we can get a simple empty sqlite database"""
    yo_config = config.YoConfigManager(
        None,
        defaults={
            'database': {
                'provider': 'sqlite',
                'init_schema': '0'
            },
            'sqlite': {
                'filename': ':memory:'
            }
        })
    yo_db = db.YoDatabase(yo_config)
    assert len(yo_db.engine.table_names()) == 0


def test_schema_sqlite():
    """Test init_schema creates empty tables"""
    yo_config = config.YoConfigManager(
        None,
        defaults={
            'database': {
                'provider': 'sqlite',
                'init_schema': '1'
            },
            'sqlite': {
                'filename': ':memory:'
            }
        })
    yo_db = db.YoDatabase(yo_config)
    assert len(yo_db.engine.table_names()) > 0
    m = MetaData()
    m.reflect(bind=yo_db.engine)
    for table in m.tables.values():
        with yo_db.acquire_conn() as conn:
            query = table.select().where(True)
            response = conn.execute(query).fetchall()
            assert len(response) == 0


@mysql_test
@no_docker
def test_schema_mysql():
    """Test init_schema with MySQL"""
    server = MySQLServer(db_name='yo_test', db_user='yo_test', db_pass='1234')
    server.wait()
    yo_config = config.YoConfigManager(
        None,
        defaults={
            'database': {
                'provider': 'mysql',
                'init_schema': '1'
            },
            'mysql': {
                'username': 'yo_test',
                'password': '1234',
                'database': 'yo_test'
            }
        })
    yo_db = db.YoDatabase(yo_config)
    assert len(yo_db.engine.table_names()) > 0
    m = MetaData()
    m.reflect(bind=yo_db.engine)
    for table in m.tables.values():
        with yo_db.acquire_conn() as conn:
            query = table.select().where(True)
            response = conn.execute(query).fetchall()
            assert len(response) == 0
    server.stop()


@mysql_test
@no_docker
def test_initdata_mysql():
    """Test we can pass initdata in from the kwarg with MySQL"""

    server = MySQLServer(db_name='yo_test', db_user='yo_test', db_pass='1234')
    server.wait()
    yo_config = config.YoConfigManager(
        None,
        defaults={
            'database': {
                'provider': 'mysql',
                'init_schema': '1'
            },
            'mysql': {
                'username': 'yo_test',
                'password': '1234',
                'database': 'yo_test'
            }
        })
    test_initdata = gen_initdata()
    yo_db = db.YoDatabase(yo_config, initdata=test_initdata)
    results = yo_db.get_user_transports('testuser1337')
    server.stop()
    assert results == TESTUSER_TRANSPORTS


def test_initdata_param():
    """Test we can pass initdata in from the kwarg"""
    yo_config = config.YoConfigManager(
        None,
        defaults={
            'database': {
                'provider': 'sqlite',
                'init_schema': '1'
            },
            'sqlite': {
                'filename': ':memory:'
            }
        })
    test_initdata = gen_initdata()
    yo_db = db.YoDatabase(yo_config, initdata=test_initdata)
    results = yo_db.get_user_transports('testuser1337')
    assert results == TESTUSER_TRANSPORTS


def test_initdata_file():
    """Basic sanity check for init.json"""
    yo_config = config.YoConfigManager(
        None,
        defaults={
            'database': {
                'provider': 'sqlite',
                'init_schema': '1',
                'init_data': '%s/../data/mockdata.json' % source_code_path
            },
            'sqlite': {
                'filename': ':memory:'
            }
        })
    yo_db = db.YoDatabase(yo_config)
    # this is just a "no exceptions were thrown" sanity check
