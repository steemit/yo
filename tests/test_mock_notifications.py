import pytest

from yo import mock_notifications


def test_create_mockdata():
    """Test basic mock data creation"""
    mockdata = mock_notifications.YoMockData()


def test_simple_get_notifications():
    """Test get_notifications actually returns data"""
    mockdata = mock_notifications.YoMockData()
    notifications = mockdata.get_notifications(username='test_user')
    assert len(notifications) > 0
