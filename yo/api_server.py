from .base_service import YoBaseService 
from .db import user_transports_table
from .utils import needs_auth
import asyncio
import json
import steem
import hashlib
from steem.account import Account
import json
import os

import logging
logger = logging.getLogger(__name__)

from yo import jsonrpc_auth



class YoAPIServer(YoBaseService):
   service_name='api_server'
   q = asyncio.Queue()

   @needs_auth
   async def api_enable_transports(self,username=None,transports={},orig_req=None,yo_db=None,**kwargs):
         for k,v in transports.items():
             logger.debug('Updating sub data for %s with %s' % (k,v))
             yo_db.update_subdata(username,transport_type=v[0],notify_type=k,sub_data=v[1])
         return {'status':'OK',
                 'source_commit': os.environ.get('SOURCE_COMMIT'),
                 'docker_tag':os.environ.get('DOCKER_TAG')}
   @needs_auth
   async def api_get_enabled_transports(self,username=None,orig_req=None,yo_db=None,**kwargs):
         retval = []
         for row in yo_db.get_user_transports(username):
             retval.append({'transport_type':row.transport_type,
                            'notify_type'   :row.notify_type,
                            'sub_data'      :row.sub_data})
         return retval
   async def api_test_method(self,**kwargs):
       return {'status':'OK', }
   async def async_task(self,yo_app): # pragma: no cover
       yo_app.add_api_method(self.api_enable_transports,'enable_transports')
       yo_app.add_api_method(self.api_get_enabled_transports,'get_enabled_transports')
       yo_app.add_api_method(self.api_test_method,'api_test_method')
