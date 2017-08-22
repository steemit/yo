import uvloop
from aiohttp import web

import aiohttp
import asyncio

import logging
logger = logging.getLogger(__name__)


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
class YoApp:
   def __init__(self,config=None,db=None):
       self.config=config
       self.db=db
       self.services={}
       self.service_tasks={}
       self.loop = asyncio.get_event_loop()
       self.web_app = web.Application(loop=self.loop)
       self.web_app['config'] = {
          'yo_config':self.config,
          'yo_db'    :self.db
       }
       self.running = False
   async def start_background_tasks(self,app):
       logger.info('Starting tasks...')
       for k,v in self.service_tasks.items():
           logger.info('Starting %s' % k)
           self.web_app['service_task:%s' % k] = self.web_app.loop.create_task(v(self))
   def run(self):
       self.running = True
       self.web_app.on_startup.append(self.start_background_tasks)
       web.run_app(self.web_app,
                   host=self.config.get_listen_host(),
                   port=self.config.get_listen_port())
   def add_service(self,service):
       name = service.get_name()
       for k,v in service.api_methods.items():
           self.api_methods['yo.%s' % name] = v # add public API methods
       self.service_tasks[name] = service.async_task
       service.yo_app = self
       self.services[name]=service
   async def invoke_public_api(self,service,api_method,*args,**kwargs):

   async def invoke_private_api(self,service,api_method,*args,**kwargs):
       # TODO - add support for URLs other than :local:
       if not service in self.services.keys():
          return {'error':'No such service found!'}
       if not api_method in self.services[service].private_api_methods.keys():
          return {'error':'No such method in service'}
       return await self.services[service].private_api_methods[api_method](*args,**kwargs)

