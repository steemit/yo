import uvloop
from aiohttp import web

import datetime
import aiohttp
import asyncio

import logging
logger = logging.getLogger(__name__)

from jsonrpcserver.aio import methods

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from jsonrpcserver.async_methods import AsyncMethods
import json

ALLOWED_ORIGINS=['http://localhost:8080','https://steemitdev.com']

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
          'yo_db'    :self.db,
          'yo_app'   :self
       }
       self.api_methods = AsyncMethods()
       self.running = False

   async def handle_api(self,request):
         origin = request.headers['Origin']
         req_app = request.app
         request = await request.json()
         orig_request = json.dumps(request) # silly hack
         logger.debug('Incoming request: %s' % request)
         if not 'params' in request.keys(): request['params'] = {} # fix for API methods that have no params
         request['params']['yo_app']    = req_app['config']['yo_app']
         request['params']['yo_db']     = req_app['config']['yo_db']
         request['params']['yo_config'] = req_app['config']['yo_config']
         request['params']['orig_req']  = json.loads(orig_request) # needed for authentication
         request['params']['skip_auth'] = False # without this, user can pass skip_auth, which is obviously bad
         response = await self.api_methods.dispatch(request)
         return web.json_response(response,headers={'Access-Control-Allow-Methods': 'POST','Access-Control-Allow-Origin': origin})
   def add_api_method(self,func,func_name):
       logger.debug('Adding API method %s' % func_name)
       self.api_methods.add(func,name='yo.%s' % func_name)
   async def start_background_tasks(self,app):
       logger.info('Starting tasks...')
       for k,v in self.service_tasks.items():
           logger.info('Starting %s' % k)
           self.web_app['service_task:%s' % k] = self.web_app.loop.create_task(v(self))
   async def api_healthcheck(self,**kwargs):
       return({'status'  :'OK',
               'datetime':datetime.datetime.utcnow().isoformat()})
   async def healthcheck_handler(self,request):
       return web.json_response(await self.api_healthcheck())
   async def handle_options(self,request):
       origin = request.headers['Origin']
       if origin in ALLOWED_ORIGINS:
          response = web.Response(status=204,headers={'Access-Control-Allow-Methods': 'POST',
                                                      'Access-Control-Allow-Origin': origin,
                                                      'Access-Control-Allow-Headers': '*'})
       else:
          response = web.Response(status=403)
       return response
   async def setup_standard_api(self,app):
       self.add_api_method(self.api_healthcheck,'healthcheck')
       self.web_app.router.add_route('OPTIONS','/',self.handle_options)
       self.web_app.router.add_post('/', self.handle_api)
       self.web_app.router.add_get('/.well-known/healthcheck.json',self.healthcheck_handler)
   def run(self):
       self.running = True
       self.web_app.on_startup.append(self.start_background_tasks)
       self.web_app.on_startup.append(self.setup_standard_api)
       web.run_app(self.web_app,
                   host=self.config.get_listen_host(),
                   port=self.config.get_listen_port())
   def add_service(self,service):
       logger.debug('Adding service %s' % service.get_name())
       name = service.get_name()
       self.service_tasks[name] = service.async_task
       service.yo_app = self
       self.services[name]=service
       service.init_api(self)
   async def invoke_private_api(self,service,api_method,*args,**kwargs):
       # TODO - add support for URLs other than :local:
       if not service in self.services.keys():
          return {'error':'No such service found!'}
       if not api_method in self.services[service].private_api_methods.keys():
          return {'error':'No such method in service'}
       return await self.services[service].private_api_methods[api_method](*args,**kwargs)

