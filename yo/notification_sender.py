from .base_service import YoBaseService 
from .db import acquire_db_conn,notifications_table
import asyncio
import json

import logging
logger = logging.getLogger(__name__)

""" Basic design:

     1. Blockchain sender inserts notification into DB
     2. Blockchain sender triggers the notification by calling internal API method
     3. Notification sender checks if the notification is already sent or not, if not it sends to all configured transports and updates it to sent
"""

class YoNotificationSender(YoBaseService):
   service_name='notification_sender'
   q = asyncio.Queue()
   async def api_trigger_notification(self,trx_id=None):
         await self.q.put({'trx_id':trx_id})
         return {'result':'Succeeded'} # dummy for now
   async def run_send_notify(self,notification_job):
       logger.debug('run_send_notify executing! %s' % notification_job)
       # TODO: Here we need to lookup the user's notification preferences and then send them the notification if it's appropriate to do so
   async def async_task(self,yo_app):
       self.private_api_methods['trigger_notification'] = self.api_trigger_notification
       logger.info('Notification sender started')
       while True:
          try:
             notification = await self.q.get()
             logger.debug('Got request to send notification: %s' % str(notification))
             await self.run_send_notify(notification)
          except Exception as e:
             logger.exception('Exception occurred')
