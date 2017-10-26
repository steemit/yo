from yo import config
from yo import db
from unittest import mock
from sqlalchemy import select
from sqlalchemy import MetaData
from sqlalchemy import func

import os
import pytest

from .conftest import MySQLServer
import socket
import time

no_docker = pytest.mark.skipif(os.getenv('INDOCKER','0')=='1',reason='Does not work inside docker')
mysql_test = pytest.mark.skipif(os.getenv('SKIPMYSQL','0')=='1',reason='Skipping MySQL tests')
source_code_path = os.path.dirname(os.path.realpath(__file__))


@mysql_test
@no_docker
def test_run_mysql():
    """Test starting a MySQL server - this is sort of a metatest as the docker trick is used for other tests"""
    server = MySQLServer()
    server.stop()

def test_empty_sqlite():
    """Test we can get a simple empty sqlite database"""
    yo_config = config.YoConfigManager(None,defaults={'database':{'provider'   :'sqlite',
                                                                  'init_schema':'0'},
                                                      'sqlite':{'filename':':memory:'}})
    yo_db = db.YoDatabase(yo_config)
    assert len(yo_db.engine.table_names())==0

def test_schema_sqlite():
    """Test init_schema creates empty tables"""
    yo_config = config.YoConfigManager(None,defaults={'database':{'provider'   :'sqlite',
                                                                  'init_schema':'1'},
                                                      'sqlite':{'filename':':memory:'}})
    yo_db = db.YoDatabase(yo_config)
    assert len(yo_db.engine.table_names()) >0
    m = MetaData()
    m.reflect(bind=yo_db.engine)
    for table in m.tables.values():
        with yo_db.acquire_conn() as conn:
             query    = table.select().where(True)
             response = conn.execute(query).fetchall()
             assert len(response)==0

@mysql_test
@no_docker
def test_schema_mysql():
    """Test init_schema with MySQL"""
    server = MySQLServer(db_name='yo_test',db_user='yo_test',db_pass='1234')
    server.wait()
    yo_config = config.YoConfigManager(None,defaults={'database':{'provider'   :'mysql',
                                                                  'init_schema':'1'},
                                                         'mysql':{'username':'yo_test','password':'1234','database':'yo_test'}})
    yo_db = db.YoDatabase(yo_config)
    assert len(yo_db.engine.table_names()) >0
    m = MetaData()
    m.reflect(bind=yo_db.engine)
    for table in m.tables.values():
        with yo_db.acquire_conn() as conn:
             query    = table.select().where(True)
             response = conn.execute(query).fetchall()
             assert len(response)==0
    server.stop()


@pytest.mark.skip(reason="this needs to be rewritten after the transports table is redefined")
@mysql_test
@no_docker
def test_initdata_mysql():
    """Test we can pass initdata in from the kwarg with MySQL"""

    server = MySQLServer(db_name='yo_test',db_user='yo_test',db_pass='1234')
    server.wait()
    yo_config = config.YoConfigManager(None,defaults={'database':{'provider'   :'mysql',
                                                                  'init_schema':'1'},
                                                         'mysql':{'username':'yo_test','password':'1234','database':'yo_test'}})
    test_initdata = [["user_transports", {"username": "testuser", "transport_type": "email", "notify_type": "vote", "sub_data": "test@example.com"}]]
    yo_db = db.YoDatabase(yo_config,initdata=test_initdata)
    results = yo_db.get_user_transports('testuser')
    row_dict = dict(results.fetchone().items())
    for k,v in test_initdata[0][1].items():
        assert row_dict[k]==v
    assert results.fetchone() == None
    server.stop()


@pytest.mark.skip(reason="this needs to be rewritten after the transports table is redefined")
def test_initdata_param():
    """Test we can pass initdata in from the kwarg"""
    yo_config = config.YoConfigManager(None,defaults={'database':{'provider'   :'sqlite',
                                                                  'init_schema':'1'},
                                                      'sqlite':{'filename':':memory:'}})
    test_initdata = [["user_transports", {"username": "testuser", "transport_type": "email", "notify_type": "vote", "sub_data": "test@example.com"}]]
    yo_db = db.YoDatabase(yo_config,initdata=test_initdata)
    results = yo_db.get_user_transports('testuser')
    row_dict = dict(results.fetchone().items())
    for k,v in test_initdata[0][1].items():
        assert row_dict[k]==v
    assert results.fetchone() == None

def test_initdata_file():
    """Basic sanity check for init.json"""
    yo_config = config.YoConfigManager(None,defaults={'database':{'provider'   :'sqlite',
                                                                  'init_schema':'1',
                                                                  'init_data'  :'%s/../data/init.json' % source_code_path},
                                                      'sqlite':{'filename':':memory:'}})
    yo_db = db.YoDatabase(yo_config)
    # this is just a "no exceptions were thrown" sanity check


@pytest.mark.skip(reason="schema for transports is in flux right now")
def test_update_subdata():
    """Test updating subdata on a user transport"""
    yo_config = config.YoConfigManager(None,defaults={'database':{'provider'   :'sqlite',
                                                                  'init_schema':'1'},
                                                      'sqlite':{'filename':':memory:'}})
    test_initdata = [["user_transports", {"username": "testuser", "transport_type": "email", "notify_type": "vote", "sub_data": "test@example.com"}]]
    yo_db = db.YoDatabase(yo_config,initdata=test_initdata)
    yo_db.update_subdata('testuser',transport_type='email',notify_type='vote',sub_data='test2@example.com')
    updated_transport = dict(yo_db.get_user_transports('testuser',transport_type='email',notify_type='vote').fetchone().items())
    assert updated_transport['sub_data']=='test2@example.com'


@pytest.mark.skip(reason="schema for transports is in flux right now")
def test_insert_subdata():
    """Test creating new subdata for user transport"""
    yo_config = config.YoConfigManager(None,defaults={'database':{'provider'   :'sqlite',
                                                                  'init_schema':'1'},
                                                      'sqlite':{'filename':':memory:'}})
    yo_db = db.YoDatabase(yo_config)
    yo_db.update_subdata('testuser',transport_type='email',notify_type='vote',sub_data='test2@example.com')
    updated_transport = dict(yo_db.get_user_transports('testuser',transport_type='email',notify_type='vote').fetchone().items())
    assert updated_transport['sub_data']=='test2@example.com'


@pytest.mark.skip(reason="schema for transports is in flux right now")
@mysql_test
@no_docker
def test_update_subdata_mysql():
    """Test updating subdata on a user transport"""

    server = MySQLServer(db_name='yo_test',db_user='yo_test',db_pass='1234')
    server.wait()
    yo_config = config.YoConfigManager(None,defaults={'database':{'provider'   :'mysql',
                                                                  'init_schema':'1'},
                                                         'mysql':{'username':'yo_test','password':'1234','database':'yo_test'}})
    test_initdata = [["user_transports", {"username": "testuser", "transport_type": "email", "notify_type": "vote", "sub_data": "test@example.com"}]]
    yo_db = db.YoDatabase(yo_config,initdata=test_initdata)
    yo_db.update_subdata('testuser',transport_type='email',notify_type='vote',sub_data='test2@example.com')
    updated_transport = dict(yo_db.get_user_transports('testuser',transport_type='email',notify_type='vote').fetchone().items())
    assert updated_transport['sub_data']=='test2@example.com'
    server.stop()


@pytest.mark.skip(reason="schema for transports is in flux right now")
@mysql_test
@no_docker
def test_insert_subdata_mysql():
    """Test creating new subdata for user transport"""

    server = MySQLServer(db_name='yo_test',db_user='yo_test',db_pass='1234')
    server.wait()
    yo_config = config.YoConfigManager(None,defaults={'database':{'provider'   :'mysql',
                                                                  'init_schema':'1'},
                                                         'mysql':{'username':'yo_test','password':'1234','database':'yo_test'}})
    yo_db = db.YoDatabase(yo_config)
    yo_db.update_subdata('testuser',transport_type='email',notify_type='vote',sub_data='test2@example.com')
    updated_transport = dict(yo_db.get_user_transports('testuser',transport_type='email',notify_type='vote').fetchone().items())
    assert updated_transport['sub_data']=='test2@example.com'
    server.stop()
