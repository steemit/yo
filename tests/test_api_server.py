import os

import pytest

from yo import config
from yo import db
from yo import api_server

source_code_path = os.path.dirname(os.path.realpath(__file__))

def get_mockdata_db():
    """Returns a new instance of YoDatabase backed by sqlite3 memory with the mock data preloaded"""
    yo_config = config.YoConfigManager(None,defaults={'database':{'provider'   :'sqlite',
                                                                  'init_schema':'1',
                                                                  'init_data'  :'%s/../data/mockdata.json' % source_code_path},
                                                                  'sqlite':{'filename':':memory:'}})
    yo_db = db.YoDatabase(yo_config)
    return yo_db


@pytest.mark.asyncio
async def test_api_test_method():
      """Test the test method"""
      API = api_server.YoAPIServer()
      retval = await API.api_test_method()
      assert retval['status']=='OK'

@pytest.mark.asyncio
async def test_api_get_notifications():
      """Basic test of get_notifications with mocked_notifications.py stuff"""
      API = api_server.YoAPIServer()
      API.testing_allowed = True
      some_notifications = await API.api_get_notifications(username='test_user',test=True,limit=5)
      assert len(some_notifications)==5



@pytest.mark.asyncio
async def test_api_get_notifications_real():
      """Basic test of get_notifications backed by real DB"""
      API = api_server.YoAPIServer()
      API.testing_allowed = False # we only want real DB data
      db = get_mockdata_db()
      some_notifications = await API.api_get_notifications(username='test_user',limit=5)
      assert len(some_notifications)==5
