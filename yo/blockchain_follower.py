from .base_service import YoBaseService 
from .db import acquire_db_conn,notifications_table
import asyncio
import steem
from steem.blockchain import Blockchain
import json

import logging
logger = logging.getLogger(__name__)

# TODO - use reliable stream when merged into steem-python


class YoBlockchainFollower(YoBaseService):
   service_name = 'blockchain_follower'
   def handle_vote(self,op):
       vote_info=op['op'][1]
       logger.info('Vote on %s (written by %s) by %s with weight %s' % (vote_info['permlink'],
                                                                        vote_info['author'],
                                                                        vote_info['voter'],
                                                                        vote_info['weight']))
       with acquire_db_conn(self.db) as conn:
            notification_object = {'from_username':vote_info['voter'],
                                   'to_username':vote_info['author'],
                                   'json_data':json.dumps(op),
                                   'type':'vote'}
            try:
               response = conn.execute(notifications_table.insert(), **notification_object)
               logger.info('Processed notification for transaction ID %s', op['trx_id'])
            except Exception as e:
               logger.exception('Exception occured')

   async def notify(self,blockchain_op):
       """ Handle notification for a particular op
       """
       logger.debug('Got operation from blockchain: %s',str(blockchain_op))
       if blockchain_op['op'][0]=='vote':
          self.handle_vote(blockchain_op)
          # handle notifications for upvotes here based on user preferences in DB
       elif blockchain_op['op'][0]=='custom_json':
          if blockchain_op['op'][1]['id']=='follow':
             logger.info('Incoming follow operation')
             # handle follow notifications here
             pass
       # etc etc
   async def async_ops(self,loop,b):
       ops = b.stream_from()
       while True:
           yield await loop.run_in_executor(None,next,ops)
   async def async_task(self,yo_app):
       logger.info('Blockchain follower started')
       while True:
          try:
             b = Blockchain()
             while True:
               try:
                  async for op in self.async_ops(yo_app.loop,b):
                     await self.notify(op)
                     await asyncio.sleep(0)
               except Exception as e:
                   logger.exception('Exception occurred')
          except Exception as e:
              logger.exception('Exception occurred')
