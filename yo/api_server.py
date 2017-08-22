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

def needs_posting_key(func):
    def new_func(*args,**kwargs):
        if not 'authsig' in kwargs.keys():
           return {'error':'This method needs authorisation with your posting key'}
        if not 'raw_json' in kwargs.keys():
           return {'error':'Internal error!'}
        digest  = hashlib.sha256(kwargs['raw_json']).digest()
        account = Account(kwargs['username'])
        posting_keys = []
        for auth in account['posting']['key_auths']: posting_keys.append(auth[0])
        # TODO - implement auth verification here
    return func

class YoAPIServer(YoBaseService):
   service_name='api_server'
   q = asyncio.Queue()
   async def api_update_preferences(self,username=None,new_preferences={},raw_json=None):
       pass
   async def async_task(self,yo_app):
       self.api_methods['update_preferences'] = needs_posting_key(self.api_update_preferences)
