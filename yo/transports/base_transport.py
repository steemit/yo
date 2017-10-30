# coding=utf-8
""" Base transport class
"""
import logging

logger = logging.getLogger(__name__)
import json

class BaseTransport:
   def send_notification(self,to_subdata=None,to_username=None,notify_type=None,data=None):
       """ Sends a notification to a specific user

       Keyword args:
          to_subdata:       the subscription data for this transport
          to_username(str): the user we're sending the notification to, not necessarily used by all transports
          notify_type(str): the type of notification we're sending
          data(dict):       a dictionary containing the raw data for the notification

       Note:
          the default implementation simply logs the notification at level LOG_INFO
       """
       logger.info('BaseTransport:send_notification sent notification of type %s to %s, summary: %s' % (notify_type,str(to_subdata),json.dumps(data)))
