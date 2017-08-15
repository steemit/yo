""" Base transport class
"""
import logging

logger = logging.getLogger(__name__)


class BaseTransport:
   def __init__(self):
       # TODO - config and stuff here
       pass
   def send_notification(self,to_user,notify_type='message',data={},msg_summary=None):
       """ Sends a notifcation to a specific user

       Keyword args:
          to_user(str):     an identifier for the end user destination
          notify_type(str): the type of notification we're sending
          data(dict):       a dictionary containing the raw data for the notification
          msg_summary(str): a human-readable summary of the notification, ignored if None

       Note:
          the default implementation simply logs the notification at level LOG_INFO
       """
       logger.info('BaseTransport:send_notification sent notification of type %s to user %s, summary: %s' % (notify_type,msg_summary),extra=data)

