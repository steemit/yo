import pytest

from yo import api_server

@pytest.mark.asyncio
async def test_api_test_method():
      """Test the test method"""
      API = api_server.YoAPIServer()
      retval = await API.api_test_method()
      assert retval['status']=='OK'
