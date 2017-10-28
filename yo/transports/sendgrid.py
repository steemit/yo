# coding=utf-8
""" Sendgrid transport class
"""
import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *

from .base_transport import BaseTransport

logger = logging.getLogger(__name__)


class SendGridTransport(BaseTransport):
   def __init__(self,sendgrid_privkey):
       """ Transport implementation for sendgrid

       Args:
           sendgrid_privkey(str): the private key for sendgrid
       """
       self.privkey = sendgrid_privkey
       self.sg = SendGridAPIClient(apikey=sendgrid_privkey)
   def send_notification(self,to_subdata=None,to_username=None,notify_type=None,data=None):
       """ Sends a notification to a specific user

       Keyword args:
          to_subdata:       the subscription data for this transport
          to_username(str): the user we're sending to
          notify_type(str): the type of notification we're sending
          data(dict):       a dictionary containing the raw data for the notification

       Note:
          the subscription data for sendgrid is simply an email address
       """
       logger.debug('SendGrid sending notification to %s' % to_subdata)
       from_email = Email("no-reply-yo@steemit.com")
       to_email = Email(to_subdata)
       if notify_type=='vote':
          vote_info    = data['op'][1]
          subject      = "%s has upvoted your post or comment" % vote_info['voter']
          text_content = 'Your comment or post %s has been upvoted by %s' % (vote_info['permlink'],vote_info['voter'])
       else:
          logger.error('SendGrid transport doesn\'t know about notification type %s' % notify_type)
          return
       content = Content("text/plain", text_content)
       mail = Mail(from_email, subject, to_email, content)
       response = self.sg.client.mail.send.post(request_body=mail.get())
       logger.debug('SendGrid response code %s'    % response.status_code)
       logger.debug('SendGrid response body %s'    % response.body)
       logger.debug('SendGrid response headers %s' % str(response.headers))
