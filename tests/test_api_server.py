import os

import pytest

from yo import config
from yo import db
from yo import api_server

from .conftest import MySQLServer

source_code_path = os.path.dirname(os.path.realpath(__file__))
no_docker = pytest.mark.skipif(os.getenv('INDOCKER','0')=='1',reason='Does not work inside docker')
mysql_test = pytest.mark.skipif(os.getenv('SKIPMYSQL','0')=='1',reason='Skipping MySQL tests')

def get_mockdata_db(use_mysql=False,mysql_params={}):
    """Returns a new instance of YoDatabase backed by sqlite3 memory with the mock data preloaded"""
    db_defaults = {'database':{'init_data'  :'%s/../data/mockdata.json' % source_code_path,
                               'init_schema':'1'}}
    if use_mysql:
       db_defaults['database']['provider'] = 'mysql'
       db_defaults['mysql']                = mysql_params
    else:
       db_defaults['database']['provider'] = 'sqlite'
       db_defaults['sqlite']               = {'filename':':memory:'}
    yo_config = config.YoConfigManager(None,defaults=db_defaults)
    yo_db = db.YoDatabase(yo_config)
    return yo_db

@pytest.mark.asyncio
async def test_api_get_notifications():
      """Basic test of get_notifications with mocked_notifications.py stuff"""
      API = api_server.YoAPIServer()
      API.testing_allowed = True
      some_notifications = await API.api_get_notifications(username='test_user',test=True,limit=5)
      assert len(some_notifications)==5

@pytest.mark.asyncio
async def test_api_get_notifications_sqlite():
      """Basic test of get_notifications backed by sqlite3"""
      API = api_server.YoAPIServer()
      API.testing_allowed = False # we only want real DB data
      db = get_mockdata_db()
      some_notifications = await API.api_get_notifications(username='test_user',limit=5,yo_db=db)
      assert len(some_notifications)==5

@no_docker
@mysql_test
@pytest.mark.asyncio
async def test_api_get_notifications_mysql():
      """Basic test of get_notifications backed by MySQL"""
      API = api_server.YoAPIServer()
      API.testing_allowed = False # we only want real DB data

      server = MySQLServer(db_name='yo_test',db_user='yo_test',db_pass='1234')
      server.wait()
      db = get_mockdata_db(use_mysql=True,mysql_params={'username':'yo_test','password':'1234','database':'yo_test'})

      some_notifications = await API.api_get_notifications(username='test_user',limit=5,yo_db=db)
      server.stop()
      assert len(some_notifications)==5

@no_docker
@mysql_test
@pytest.mark.asyncio
async def test_api_get_set_transports_mysql():
      """Test get and set transports backed by MySQL with simple non-default transports"""
      API = api_server.YoAPIServer()
      API.testing_allowed = False # we only want real DB data

      server = MySQLServer(db_name='yo_test',db_user='yo_test',db_pass='1234')
      server.wait()
      db = get_mockdata_db(use_mysql=True,mysql_params={'username':'yo_test','password':'1234','database':'yo_test'})

      simple_transports_obj = {'email':{'notification_types':['vote','comment'],
                                        'sub_data':'testuser1337@example.com'},
                               'wwwpoll':{'notification_types':['mention','post_reply'],
                                          'sub_data':{'stuff':'not here by default'}}}

      resp = await API.api_set_transports(username='testuser1337',transports=simple_transports_obj,test=False,yo_db=db)
      assert resp == simple_transports_obj

      resp = await API.api_get_transports(username='testuser1337',test=False,yo_db=db)
      assert resp == simple_transports_obj
