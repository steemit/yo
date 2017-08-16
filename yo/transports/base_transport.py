""" Base transport class
"""
import logging

logger = logging.getLogger(__name__)


class BaseTransport:
   def __init__(self):
       # TODO - config and stuff here
       pass
   def send_notification(self,to_uid=None,notify_type='message',data={},msg_summary=None):
       """ Sends a notification to a specific user

       Keyword args:
          to_uid(str):      user's UID we're sending to
          notify_type(str): the type of notification we're sending
          data(dict):       a dictionary containing the raw data for the notification
          msg_summary(str): a human-readable summary of the notification, ignored if None

       Note:
          the default implementation simply logs the notification at level LOG_INFO
       """
       logger.info('BaseTransport:send_notification sent notification of type %s to user %s, summary: %s' % (notify_type,msg_summary),extra=data)

