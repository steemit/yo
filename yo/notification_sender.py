from .base_service import YoBaseService 
from .db import notifications_table,user_transports_table
import asyncio
import json

from .ratelimits import check_ratelimit
from .transports import base_transport
from .transports import sendgrid
from .transports import twilio
import datetime
import logging
logger = logging.getLogger(__name__)

""" Basic design:

     1. Blockchain sender inserts notification into DB
     2. Blockchain sender triggers the notification by calling internal API method
     3. Notification sender checks if the notification is already sent or not, if not it sends to all configured transports and updates it to sent
"""



class YoNotificationSender(YoBaseService):
   service_name='notification_sender'

   def get_user_transports(self,db_conn,username,notify_type):
       """ Returns a list of tuples of (transport,sub_data)
       """
       retval = []
       query = user_transports_table.select().where(user_transports_table.c.username==username).where(user_transports_table.c.notify_type==notify_type)
    
       for row in db_conn.execute(query):
           if row['transport_type'] in self.configured_transports.keys():
              retval.append((self.configured_transports[row['transport_type']],row['sub_data']))
       return retval
   async def api_trigger_notification(self,username=None):
         logger.info('api_trigger_notification invoked for %s' % username)
         await self.run_send_notify({'to_username':username})
         return {'result':'Succeeded'} # dummy for now
   async def run_send_notify(self,notification_job):
         logger.debug('run_send_notify executing! %s' % notification_job)
         with self.db.acquire_conn() as conn:
              query = notifications_table.select().where(notifications_table.c.to_username == notification_job['to_username'])
              # TODO - add check for already sent
              select_response = conn.execute(query)
              for row in select_response:
                  row_dict = dict(row.items())
                  if not check_ratelimit(self.db,row_dict):
                     logger.debug('Skipping sending of notification for failing rate limit check: %s' % str(row))
                     continue
                  logger.debug('>>>>>> Sending new notification: %s' % str(row))
                  transports = self.get_user_transports(conn,notification_job['to_username'],row['type'])
                  for t in transports:
                      logger.debug('Sending notification to transport %s' % str(t))
                      t[0].send_notification(to_subdata=t[1],notify_type=row['type'],data=json.loads(row['json_data']))
                  row_dict['sent']    = True
                  row_dict['sent_at'] = datetime.datetime.now()
                  update_query = notifications_table.update().where(notifications_table.c.nid==row.nid).values(sent=True,sent_at=datetime.datetime.now())
                  conn.execute(update_query)

   def init_api(self,yo_app):
       self.private_api_methods['trigger_notification'] = self.api_trigger_notification
       self.configured_transports={}
       if int(yo_app.config.config_data['sendgrid'].get('enabled', 0)) == 1:
           logger.info('Enabling sendgrid (email) transport')
           self.configured_transports['email'] = sendgrid.SendGridTransport(yo_app.config.config_data['sendgrid']['priv_key'])
       if int(yo_app.config.config_data['twilio'].get('enabled', 0)) == 1:
           logger.info('Enabling twilio (sms) transport')
           self.configured_transports['sms'] = twilio.TwilioTransport(
              yo_app.config.config_data['twilio']['account_sid'],
              yo_app.config.config_data['twilio']['auth_token'],
              yo_app.config.config_data['twilio']['from_number'],
           )
   async def async_task(self,yo_app):
       logger.info('Notification sender started')
