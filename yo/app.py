import uvloop
from aiohttp import web

import aiohttp
import asyncio

import logging
logger = logging.getLogger(__name__)


#asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
class YoApp:
   def __init__(self,config=None,db=None):
       self.config=config
       self.db=db
       self.services={}
       self.loop = asyncio.get_event_loop()
       self.web_app = web.Application(loop=self.loop)
       self.web_app['config'] = {
          'yo_config':self.config,
          'yo_db'    :self.db
       }
       self.running = False
   async def start_background_tasks(self,app):
       logger.info('Starting tasks...')
       for k,v in self.services.items():
           logger.info('Starting %s' % k)
           self.web_app[k] = self.web_app.loop.create_task(v(self))
   def run(self):
       self.running = True
       self.web_app.on_startup.append(self.start_background_tasks)
       web.run_app(self.web_app,
                   host=self.config.get_listen_host(),
                   port=self.config.get_listen_port())
   def add_service(self,service):
       self.services[service.get_name()] = service.async_task
