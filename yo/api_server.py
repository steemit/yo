from .base_service import YoBaseService 
from .db import user_transports_table
from .mock_notifications import YoMockData
from .utils import needs_auth
import asyncio
import json
import steem
import hashlib
from steem.account import Account
import json
import datetime

import logging
logger = logging.getLogger(__name__)

class YoAPIServer(YoBaseService):
   service_name='api_server'
   q = asyncio.Queue()

   test_notifications = YoMockData()

   async def api_enable_transports(self,username=None,transports={},orig_req=None,yo_db=None,**kwargs):
         """ Enables/updates selected transports

         Keyword args:
            username(str):    The user to update
            transports(dict): A dictionary mapping notification types to [transport_type,sub_data] values

         Returns:
            dict: {'status':'OK'} on success
         """
         for k,v in transports.items():
             logger.debug('Updating sub data for %s with %s' % (k,v))
             yo_db.update_subdata(username,transport_type=v[0],notify_type=k,sub_data=v[1])
         return {'status':'OK'}
   async def api_get_enabled_transports(self,username=None,orig_req=None,yo_db=None,**kwargs):
         retval = []
         for row in yo_db.get_user_transports(username):
             retval.append({'transport_type':row.transport_type,
                            'notify_type'   :row.notify_type,
                            'sub_data'      :row.sub_data})
         return retval
   async def api_get_notifications(self,username=None,created_before=None,updated_after=None,read=None,notify_type=None,limit=30,test=False,orig_req=None,yo_db=None,**kwargs):
       """ Get all notifications since the specified time

       Keyword args:
          username(str): The username to query for
          created_before(str): ISO8601-formatted timestamp
          updated_after(str): ISO8601-formatted timestamp
          read(bool): If set, only returns notifications with read flag set to this value
          notify_type(str): The notification type to return
          limit(int): The maximum number of notifications to return, defaults to 30
          test(bool): If True, uses mock data only instead of talking to the database backend

       Returns:
          list: list of notifications represented in dictionary format
       """
       if test:
          return self.test_notifications.get_notifications(username=username,created_before=created_before,updated_after=updated_after,notify_type=notify_type,read=read)
       else: 
          # TODO  - implement real thing here
         return []
   async def api_mark_read(self,ids=[],orig_req=None,test=False,yo_db=None,**kwargs):
       """ Mark a list of notifications as read

       Keyword args:
           ids(list): List of notifications to mark read
       
       Returns:
           list: list of notifications updated
       """
       if test:
          for notify_id in ids:
              self.test_notifications.mark_notification_read(notify_id)
       else:
          return []
   async def api_mark_seen(self,ids=[],orig_req=None,test=False,yo_db=None,**kwargs):
       """ Mark a list of notifications as seen

       Keyword args:
           ids(list): List of notifications to mark seen

       Returns:
           list: list of notifications updated
       """
       if test:
          for notify_id in ids:
              self.test_notifications.mark_notification_seen(notify_id)
       else:
          return []
   async def api_reset_test_data(self,**kwargs):
       self.test_notifications.reset()
   async def api_test_method(self,**kwargs):
       return {'status':'OK'}
   async def async_task(self,yo_app): # pragma: no cover
       yo_app.add_api_method(self.api_enable_transports,'enable_transports')
       yo_app.add_api_method(self.api_get_enabled_transports,'get_enabled_transports')
       yo_app.add_api_method(self.api_get_notifications,'get_notifications')
       yo_app.add_api_method(self.api_reset_test_data,'reset_test_data')
       yo_app.add_api_method(self.api_mark_read,'mark_read')
       yo_app.add_api_method(self.api_test_method,'api_test_method')
