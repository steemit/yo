from .base_service import YoBaseService 
from .db import acquire_db_conn,notifications_table
import asyncio
import steem
from steem.blockchain import Blockchain
import json

import logging
logger = logging.getLogger(__name__)

# TODO - use reliable stream when merged into steem-python

# Basically this service just follows the blockchain and inserts into the DB then triggers the notification sender to send the actual notification

class YoBlockchainFollower(YoBaseService):
   service_name = 'blockchain_follower'
   async def handle_vote(self,op):
       retval = True
       vote_info=op['op'][1]
       logger.debug('Vote on %s (written by %s) by %s with weight %s' % (vote_info['permlink'],
                                                                        vote_info['author'],
                                                                        vote_info['voter'],
                                                                        vote_info['weight']))
       with acquire_db_conn(self.db) as conn:
            notification_object = {'trx_id':op['trx_id'],
                                  'from_username':vote_info['voter'],
                                  'to_username':vote_info['author'],
                                  'json_data':json.dumps(op),
                                  'sent':False,
                                  'type':'vote'}
            try:
               tx = conn.begin()
               insert_response = conn.execute(notifications_table.insert(), **notification_object)
               logger.debug('Processed vote notification for transaction ID %s' % op['trx_id'])
               tx.commit()
            except Exception as e:
               tx.rollback()
               logger.exception('Exception occured while processing transaction ID %s' % op['trx_id'])
               retval = False
       if retval:
          sender_response = await self.yo_app.invoke_private_api('notification_sender','trigger_notification',username=notification_object['to_username'])
       return retval

   async def notify(self,blockchain_op):
       """ Handle notification for a particular op
       """
       logger.debug('Got operation from blockchain: %s',str(blockchain_op))
       if blockchain_op['op'][0]=='vote':
          return await self.handle_vote(blockchain_op)
          # handle notifications for upvotes here based on user preferences in DB
       elif blockchain_op['op'][0]=='custom_json':
          if blockchain_op['op'][1]['id']=='follow':
             logger.debug('Incoming follow operation')
             # handle follow notifications here
             pass
       # etc etc
       return True # return this or the op will be requeued
   async def run_queue(self,q):
       while not q.empty():
             op = await q.get()

             resp = await self.notify(op)
             if not resp: 
                logger.debug('Re-queueing operation: %s' % str(op))
                return op
       return None
   async def async_ops(self,loop,b):
       ops = b.stream_from()
       while True:
           yield await loop.run_in_executor(None,next,ops)
   async def async_task(self,yo_app):
       queue = asyncio.Queue()
       logger.info('Blockchain follower started')
       while True:
          try:
             b = Blockchain()
             while True:
               try:
                  async for op in self.async_ops(yo_app.loop,b):
                     await queue.put(op)
                     await asyncio.sleep(0)
                     runner_resp = await self.run_queue(queue)
                     if not (runner_resp is None): queue.put(runner_resp)
               except Exception as e:
                   logger.exception('Exception occurred')
          except Exception as e:
              logger.exception('Exception occurred')
