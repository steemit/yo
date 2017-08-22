import asyncio
import steem
from steem.blockchain import Blockchain

import logging
logger = logging.getLogger(__name__)

# TODO - use reliable stream when merged into steem-python

class YoBlockchainFollower:
   def __init__(self,config=None,db=None):
       self.config=config
       self.db=db
   def get_name(self):
       return 'blockchain follower'
   async def notify(self,blockchain_op):
       """ Handle notification for a particular op
       """
       logger.debug('Got operation from blockchain')
       if blockchain_op['op'][0]=='vote':
          logger.info('Incoming vote operation')
          # handle notifications for upvotes here based on user preferences in DB
       elif blockchain_op['op'][0]=='custom_json':
          if blockchain_op['op'][1]['id']=='follow':
             logger.info('Incoming follow operation')
             # handle follow notifications here
             pass
       # etc etc
   async def async_ops(self,loop,b):
       while True:
           ops = b.stream_from()
           yield await loop.run_in_executor(None,ops.__next__)
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
