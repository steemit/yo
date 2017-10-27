import json

from yo import mock_notifications

mock_data = mock_notifications.YoMockData()

data = []

for notification in mock_data.get_notifications(limit=9999):
    notification['data'] = json.dumps(notification['data'])
    data.append(('wwwpoll', notification))

print(json.dumps(data))
