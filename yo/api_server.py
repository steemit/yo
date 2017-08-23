from .base_service import YoBaseService 
from .db import acquire_db_conn,notifications_table
import asyncio
import json
import steem
import hashlib
from steem.account import Account
from steembase.transactions import SignedTransaction
import json

import logging
logger = logging.getLogger(__name__)

class YoAPIServer(YoBaseService):
   service_name='api_server'
   q = asyncio.Queue()
   async def api_update_preferences(self,username=None,new_preferences={},raw_json=None):
       pass
   async def async_task(self,yo_app):
       self.api_methods['update_preferences'] = self.api_update_preferences
