import logging

logger = logging.getLogger(__name__)

from .base_transport import BaseTransport

from pywebpush import webpush

from yo import static_content

from yo.storage import wwwpushsubs

import json

VAPID_EMAIL='test@example.com'

class WWWPushTransport(BaseTransport):
   def __init__(self,vapid_priv_key=None,db=None):
       if vapid_priv_key is None:
          vapid_priv_key = static_content.loadfile('./wwwpush_privkey.txt')
       self.vapid_priv_key = vapid_priv_key
       self.db = db
   def send_notification(self,to_uid=None,notify_type='message',data={},msg_summary=None):
       for sub in wwwpushsubs.get_by_to_uid(self.db,to_uid):
           try:
              sub_info = json.loads(sub['push_sub_json'])
              webpush(sub_info,
                      json.dumps(data),
                      vapid_private_key = self.vapid_priv_key,
                      vapid_claims      = {'sub':VAPID_EMAIL})
           except Exception as e:
              logger.exception('Exception occurred when sending notification to browser',e,extra=sub)
