""" Base class for other services
"""

class YoBaseService:
   api_methods         = {}
   private_api_methods = {}
   service_name        = 'base'
   def __init__(self,config=None,db=None):
       self.config=config
       self.db=db
   def init_api(self,yo_app):
       pass
   def get_name(self):
       return self.service_name
   async def async_task(self,yo_app):
       """ This method will run in the background
       """
       return
