# -*- coding: utf-8 -*-
import json
import os
import argparse

import logging

import pytest

from yo.db_utils import init_db


logging.basicConfig(level='DEBUG')

@pytest.fixture
def parsed_args():
    parser = argparse.ArgumentParser(description="Steem notification service")
    parser.add_argument('--log_level',
                        default=os.environ.get('LOG_LEVEL', 'INFO'))
    parser.add_argument('--steemd_url', default=os.environ.get('STEEMD_URL',
                                                               'https://api.steemit.com'))
    parser.add_argument('--database_url',
                        default=os.environ.get('DATABASE_URL', 'sqlite://'))
    parser.add_argument('--sendgrid_priv_key',
                        default=os.environ.get('SENDGRID_PRIV_KEY', None))
    parser.add_argument('--sendgrid_templates_dir',
                        default=os.environ.get('SENDGRID_TEMPLATES_DIR',
                                               'mail_templates'))
    parser.add_argument('--twilio_account_sid',
                        default=os.environ.get('TWILIO_ACCOUNT_SID', None))
    parser.add_argument('--twilio_auth_token',
                        default=os.environ.get('TWILIO_AUTH_TOKEN', None))
    parser.add_argument('--twilio_from_number',
                        default=os.environ.get('TWILIO_FROM_NUMBER', None))
    parser.add_argument('--steemd_start_block',
                        default=os.environ.get('STEEMD_START_BLOCK', None))
    parser.add_argument('--http_host',
                        default=os.environ.get('HTTP_HOST', '0.0.0.0'))
    parser.add_argument('--http_port', type=int,
                        default=os.environ.get('HTTP_PORT', 8080))
    return parser.parse_args([])


@pytest.fixture
def basic_mock_app(parsed_args, sqlite_db):
    class MockApp:
        def __init__(self, db):
            self.db = db
            self.config = parsed_args
    return MockApp(sqlite_db)

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
                'reward_type': 'curation',
                'item': dict(
                    author='test_user',
                    category='test',
                    permlink='test-post',
                    summary='A test post'),
                'amount': dict(SBD=6.66, SP=13.37)
            },
        }
    ]
