from .base_service import YoBaseService 
from .db import acquire_db_conn,user_transports_table
import asyncio
import json
import steem
import hashlib
from steem.account import Account
import json

import logging
logger = logging.getLogger(__name__)

from yo import jsonrpc_auth



class YoAPIServer(YoBaseService):
   service_name='api_server'
   q = asyncio.Queue()
   async def api_enable_transports(self,username=None,transports={},orig_req=None,yo_db=None,**kwargs):
         if not jsonrpc_auth.verify_request(orig_req,username):
            return {'error':'Request could not be authenticated'}
         for k,v in transports.items():
             logger.debug('Updating sub data for %s with %s' % (k,v))
             
             # if we don't already have an entry for each transport, add one now
             # otherwise, we simply update the sub_data
             # TODO - add support for multiple subs
             with acquire_db_conn(yo_db) as conn:
                  query = user_transports_table.select().where(user_transports_table.c.username == username).where(user_transports_table.c.notify_type == k)
                  select_response = conn.execute(query)
                  if select_response.rowcount>0: # we need to update the sub_data
                     update_query = user_transports_table.update(sub_data=v[1]).where(user_transports_table.c.username==username).where(user_transports_table.c.notify_type==k)
                  else: # we need to create a new row
                     update_query = user_transports_table.insert().values(username=username,
                                                                          notify_type=k,
                                                                          transport_type=v[0],
                                                                          sub_data=v[1])
                  conn.execute(update_query)

         return {'status':'OK'}
   async def api_get_enabled_transports(self,username=None,orig_req=None,yo_db=None,**kwargs):
         if not jsonrpc_auth.verify_request(orig_req,username):
            return {'error':'Request could not be authenticated'}
         retval = []
         with acquire_db_conn(yo_db) as conn:
              query = user_transports_table.select().where(user_transports_table.c.username == username)
              select_response = conn.execute(query)
              for row in select_response:
                  retval.append({'transport_type':row.transport_type,
                                 'notify_type'   :row.notify_type,
                                 'sub_data'      :row.sub_data})
         return retval
   async def api_test_method(self,**kwargs):
       return {'status':'OK'}
   async def async_task(self,yo_app):
       yo_app.add_api_method(self.api_enable_transports,'enable_transports')
       yo_app.add_api_method(self.api_get_enabled_transports,'get_enabled_transports')
       yo_app.add_api_method(self.api_test_method,'api_test_method')
