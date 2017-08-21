import uvloop
from aiohttp import web

import aiohttp
import asyncio

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
class YoApp:
   def __init__(self,config=None,db=None):
       self.config=config
       self.db=db
       self.services=set()
       self.loop = asyncio.get_event_loop()
       self.web_app = web.Application(loop=self.loop)
       self.web_app['config'] = {
          'yo_config':self.config,
          'yo_db'    :self.yo_db
       }
       self.running = False
   def run(self):
       self.running = True
       web.run_app(self.web_app,
                   host=self.config.get_listen_host(),
                   port=self.config.get_listen_port())
   def add_service(self,service):
       self.services.add(service)
       self.web_app[service.get_name()] = self.web_app.loop.create_task(service.async_task)
