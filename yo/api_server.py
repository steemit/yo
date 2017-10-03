from .base_service import YoBaseService 
from .db import user_transports_table
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

from yo import jsonrpc_auth

def mock_notification():
    return {notification_id:1337,
            read:False,
            shown:False,
            notification_type: 'VOTE',
            created:datetime.datetime.now().isoformat(),
            author:'test',
            data:{}}

class YoAPIServer(YoBaseService):
   service_name='api_server'
   q = asyncio.Queue()

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
   @needs_auth
   async def api_get_enabled_transports(self,username=None,orig_req=None,yo_db=None,**kwargs):
         retval = []
         for row in yo_db.get_user_transports(username):
             retval.append({'transport_type':row.transport_type,
                            'notify_type'   :row.notify_type,
                            'sub_data'      :row.sub_data})
         return retval
   async def api_get_notifications(self,username=None,since=None,orig_req=None,yo_db=None):
       """ Get all notifications since the specified time

       Keyword args:
          username(str): The username to query for
          since(str):    The iso8601 formatted timestamp to query since

       Returns:
          list: list of notifications
       """
       return [mock_notification()]
   async def api_test_method(self,**kwargs):
       return {'status':'OK'}
   async def async_task(self,yo_app): # pragma: no cover
       yo_app.add_api_method(self.api_enable_transports,'enable_transports')
       yo_app.add_api_method(self.api_get_enabled_transports,'get_enabled_transports')
       yo_app.add_api_method(self.api_get_notifications,'get_notifications')
       yo_app.add_api_method(self.api_test_method,'api_test_method')
