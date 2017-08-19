import logging

logger = logging.getLogger(__name__)

from .base_transport import BaseTransport

import sendgrid

from sendgrid.helpers.mail import *

from yo import static_content

from yo.storage import emailsubs
from yo.storage import users

import json

SENDGRID_TEMPLATES={'message':'1d6c3a6a-cf9c-4cff-9dca-6d3992d6548e'}

class SendgridEmailTransport(BaseTransport):
   def __init__(self,sendgrid_privkey=None,db=None):
       if sendgrid_privkey is None:
          sendgrid_privkey = static_content.loadfile('./sendgrid_privkey.txt')
       self.sendgrid_priv_key = sendgrid_privkey
       self.db = db
       self.sg = sendgrid.SendGridAPIClient(apikey=self.sendgrid_priv_key)
   async def send_notification(self,to_uid=None,notify_type='message',data={},msg_summary=None):
       user_profile = await users.get(self.db,to_uid)
       email_subs = await emailsubs.get_by_to_uid(self.db,to_uid)
       for sub in email_subs:
           try:
              sendgrid_template_name=SENDGRID_TEMPLATES[notify_type]
              sendgrid_tousername   =user_profile['name']
              sendgrid_toemail      =sub['email_address']
              sendgrid_fromemail    ='yo@steemit.com'
              mail = Mail(Email(sendgrid_fromemail), 'Yo notification', Email(sendgrid_toemail), Content('','text/html'))
              for k,v in data:
                  mail.personalizations[0].add_substitution(Substitution('-%s-' % k, str(v)))
           except Exception as e:
              logger.exception('Exception occurred when sending notification to sendgrid',e,extra=sub)
