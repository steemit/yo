# -*- coding: utf-8 -*-









def test_schema_sqlite(sqlite_db):
    """Test init_schema creates empty tables"""
    yo_db = sqlite_db
    m = MetaData()
    m.create_all(bind=yo_db.engine)
    for table in m.tables.values():
        with yo_db.acquire_conn() as conn:
            query = table.select().where(True)
            response = conn.execute(query).fetchall()
            assert len(response) == 0, '%s should have 0 rows' % table


def test_create_notification(sqlite_db):
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
    test_data = {
        'json_data':     yojson.dumps(vote_data),
        'to_username': 'testuser1337',
        'from_username': 'testuser1336',
        'notify_type': 'vote',
        'trx_id': '123abc'
    }

    yo_db = sqlite_db
    retval = yo_db.create_db_notification(**test_data)
    assert retval is True
    result = yo_db.get_db_notifications(to_username='testuser1337',
                                        limit=2)
    assert len(result) == 1
    result = result[0]

    assert result['notify_type'] == 'vote'
    assert result['to_username'] == 'testuser1337'
    assert result['from_username'] == 'testuser1336'
    assert yojson.loads(result['json_data']) == vote_data
    assert isinstance(result['created'], datetime)

    # notifications only columns
    assert result['trx_id'] == '123abc'


def test_create_wwwpoll_notification(sqlite_db):
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
    test_data = {
        'json_data':     yojson.dumps(vote_data),
        'from_username': 'testuser1336',
        'to_username': 'testuser1337',
        'notify_type': 'vote'
    }

    yo_db = sqlite_db
    retval = yo_db.create_wwwpoll_notification(**test_data)
    assert retval is True
    result = yo_db.get_wwwpoll_notifications(to_username='testuser1337',
                                             limit=2)
    assert len(result) == 1
    result = result[0]

    assert result['notify_type'] == 'vote'
    assert result['to_username'] == 'testuser1337'
    assert yojson.loads(result['json_data']) == vote_data
    assert isinstance(result['created'], datetime)

    # wwwpoll only columns
    assert result['read'] == False
    assert result['shown'] == False


def test_get_notifications(sqlite_db):
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
    test_data = {
        'json_data':     yojson.dumps(vote_data),
        'to_username': 'testuser1337',
        'from_username': 'testuser1336',
        'notify_type': 'vote',
        'trx_id': '123abc'
    }

    yo_db = sqlite_db
    retval = yo_db.create_db_notification(**test_data)
    assert retval is True
    result = yo_db.get_db_notifications(to_username='testuser1337',
                                        limit=2)
    assert len(result) == 1
    result = result[0]

    assert result['notify_type'] == 'vote'
    assert result['to_username'] == 'testuser1337'
    assert result['from_username'] == 'testuser1336'
    assert yojson.loads(result['json_data']) == vote_data
    assert isinstance(result['created'], datetime)

    # notifications only columns
    assert result['trx_id'] == '123abc'


def test_get_wwwpoll_notifications(sqlite_db):
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
    test_data = {
        'json_data':     yojson.dumps(vote_data),
        'from_username': 'testuser1336',
        'to_username': 'testuser1337',
        'notify_type': 'vote',
    }

    yo_db = sqlite_db
    retval = yo_db.create_wwwpoll_notification(**test_data)
    assert retval is True
    result = yo_db.get_wwwpoll_notifications(to_username='testuser1337',
                                             limit=2)
    assert len(result) == 1
    result = result[0]

    assert result['notify_type'] == 'vote'
    assert result['to_username'] == 'testuser1337'
    assert yojson.loads(result['json_data']) == vote_data
    assert isinstance(result['created'], datetime)

    # wwwpoll only columns
    assert result['read'] == False
    assert result['shown'] == False


def test_wwpoll_mark_shown(sqlite_db):
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
    test_data = {
        'json_data':     yojson.dumps(vote_data),
        'from_username': 'testuser1336',
        'to_username': 'testuser1337',
        'notify_type': 'vote'
    }

    yo_db = sqlite_db
    _ = yo_db.create_wwwpoll_notification(**test_data)
    result = yo_db.get_wwwpoll_notifications(to_username='testuser1337')[0]
    assert result['shown'] is False

    _ = yo_db.wwwpoll_mark_shown(result['nid'])
    assert _ is True

    result = yo_db.get_wwwpoll_notifications(to_username='testuser1337')[0]
    assert result['shown'] is True


def test_wwpoll_mark_unshown(sqlite_db):
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
    test_data = {
        'json_data':     yojson.dumps(vote_data),
        'from_username': 'testuser1336',
        'to_username': 'testuser1337',
        'notify_type': 'vote',
        'shown':         True
    }

    yo_db = sqlite_db
    _ = yo_db.create_wwwpoll_notification(**test_data)
    result = yo_db.get_wwwpoll_notifications(to_username='testuser1337')[0]
    assert result['shown'] is True

    _ = yo_db.wwwpoll_mark_unshown(result['nid'])
    assert _ is True

    result = yo_db.get_wwwpoll_notifications(to_username='testuser1337')[0]
    assert result['shown'] is False


def test_wwpoll_mark_read(sqlite_db):
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
    test_data = {
        'json_data':     yojson.dumps(vote_data),
        'from_username': 'testuser1336',
        'to_username': 'testuser1337',
        'notify_type': 'vote'
    }

    yo_db = sqlite_db
    _ = yo_db.create_wwwpoll_notification(**test_data)
    result = yo_db.get_wwwpoll_notifications(to_username='testuser1337')[0]
    assert result['read'] is False

    _ = yo_db.wwwpoll_mark_read(result['nid'])
    assert _ is True

    result = yo_db.get_wwwpoll_notifications(to_username='testuser1337')[0]
    assert result['read'] is True


def test_wwpoll_mark_unread(sqlite_db):
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
    test_data = {
        'json_data':     yojson.dumps(vote_data),
        'from_username': 'testuser1336',
        'to_username': 'testuser1337',
        'notify_type': 'vote',
        'read':          True
    }

    yo_db = sqlite_db
    _ = yo_db.create_wwwpoll_notification(**test_data)
    result = yo_db.get_wwwpoll_notifications(to_username='testuser1337')[0]
    assert result['read'] is True

    _ = yo_db.wwwpoll_mark_unread(result['nid'])
    assert _ is True

    result = yo_db.get_wwwpoll_notifications(to_username='testuser1337')[0]
    assert result['read'] is False


def test_create_user(sqlite_db):
    yo_db = sqlite_db
    result = yo_db.create_user(username='testuser')
    assert result is True
    transports = yo_db.get_user_transports(username='testuser')
    assert transports == DEFAULT_USER_TRANSPORT_SETTINGS


def test_get_user_transports_user_doesnt_exist(sqlite_db):
    yo_db = sqlite_db
    transports = yo_db.get_user_transports(username='testuser')
    assert transports == DEFAULT_USER_TRANSPORT_SETTINGS


def test_get_user_transports_user_exists(sqlite_db):
    yo_db = sqlite_db
    result = yo_db.set_user_transports(username='testuser',
                                       transports=TEST_USER_TRANSPORT_SETTINGS)
    assert result is True

    transports = yo_db.get_user_transports(username='testuser')
    assert transports == TEST_USER_TRANSPORT_SETTINGS


def test_set_user_transports(sqlite_db):
    yo_db = sqlite_db
    _ = yo_db.set_user_transports(username='testuser',
                                  transports=TEST_USER_TRANSPORT_SETTINGS)

    assert yo_db.get_user_transports(username='testuser')
