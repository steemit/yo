# coding=utf-8
""" wwwpoll transport class

    This handles the notifications accessible via the API with polling (as used by condenser).
    "delivery" basically means storing the notification into the wwwpoll table where it can be polled using the API.
"""

import logging

from .base_transport import BaseTransport

logger = logging.getLogger(__name__)


class WWWPollTransport(BaseTransport):
   def __init__(self,yo_db):
       """ Transport implementation for polling interface

       Args:
           yo_db: instance of YoDatabase to use
       """
       self.db = yo_db
   def send_notification(self,to_subdata=None,to_username=None,notify_type=None,data=None):
       """ Sends a notification to a specific user

       Keyword args:
          to_subdata:       the subscription data for this transport
          to_username(str): the username for the user we're sending to
          notify_type(str): the type of notification we're sending
          data(dict):       a dictionary containing the raw data for the notification

       Note:
          the subscription data for wwwpoll is ignored at present and not used
       """
       logger.debug('wwwpoll sending notification to %s' % to_username)
       db.create_wwwpoll_notification(to_user=to_username, raw_data=data)
