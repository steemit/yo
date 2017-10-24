import json

from yo import mock_notifications

mock_data = mock_notifications.YoMockData()

data = []

for notification in mock_data.get_notifications(limit=9999):
    data.append(('yo_wwwpoll',notification))

print(json.dumps(data))
