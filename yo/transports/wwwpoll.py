""" wwwpoll transport class
    
    This handles the notifications accessible via the API with polling (as used by condenser).
    "delivery" basically means storing the notification into the wwwpoll table where it can be polled using the API.
"""

from .base_transport import BaseTransport
import logging

logger = logging.getLogger(__name__)
import json

class WWWPollTransport(BaseTransport):
   def __init__(self,yo_db):
       """ Transport implementation for polling interface

       Args:
           yo_db: instance of YoDatabase to use
       """
       self.db = yo_db
   def send_notification(self,to_subdata={},to_username=None,notify_type=None,data={}):
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
