from .base_service import YoBaseService 
from .db import acquire_db_conn,notifications_table
import asyncio
import json
import steem
import hashlib
from steem.account import Account
import json

import logging
logger = logging.getLogger(__name__)

class YoAPIServer(YoBaseService):
   service_name='api_server'
   q = asyncio.Queue()
   async def api_enable_transports(self,username=None,transports={},**kwargs):
       pass
   async def api_test_method(self,**kwargs):
       return {'status':'OK'}
   async def async_task(self,yo_app):
       yo_app.add_api_method(self.api_enable_transports,'enable_transports')
       yo_app.add_api_method(self.api_test_method,'api_test_method')
