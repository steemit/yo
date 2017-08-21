import steem
from steem.blockchain import Blockchain

# TODO - use reliable stream when merged into steem-python

class YoBlockchainFollower:
   def __init__(self,config=None,db=None):
       self.config=config
       self.db=db
   def get_name(self):
       return 'blockchain follower'
   def notify(self,blockchain_op):
       """ Handle notification for a particular op
       """
       if blockchain_op['op'][0]=='vote':
          # handle notifications for upvotes here based on user preferences in DB
          pass
       elif blockchain_op['op'][0]=='custom_json':
          if blockchain_op['op'][1]['id']=='follow':
             # handle follow notifications here
             pass
       # etc etc
   async def async_task(self,web_app):
       while True:
          try:
             b = Blockchain()
             for op in b.stream_from():
                 self.notify(op)
          except Exception as e:
             print(str(e))
