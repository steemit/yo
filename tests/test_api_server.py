import pytest

from yo import api_server
from unittest import mock

@pytest.mark.asyncio
async def test_api_test_method():
      """Test the test method"""
      API = api_server.YoAPIServer()
      retval = await API.api_test_method()
      assert retval['status']=='OK'

@pytest.mark.asyncio
async def test_api_get_enabled_transports():
      """Test get_enabled_transports"""
      API = api_server.YoAPIServer()
      mock_db = mock.Mock()
      mock_db.get_user_transports.return_value = []
      retval = await API.api_get_enabled_transports(username='testuser',yo_db=mock_db,skip_auth=True)
      mock_db.get_user_transports.assert_called_with('testuser')
      assert retval==[]
      row = mock.Mock()
      row.transport_type = 'email'
      row.notify_type    = 'vote'
      row.sub_data       = 'test@example.com'
      mock_db.reset_mock()
      mock_db.get_user_transports.return_value = [row]
      retval = await API.api_get_enabled_transports(username='testuser',yo_db=mock_db,skip_auth=True)
      assert retval==[{'transport_type':'email','notify_type':'vote','sub_data':'test@example.com'}]
      mock_db.get_user_transports.assert_called_with('testuser')

