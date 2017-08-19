""" Main entry point for the yo server
    
    As of now does not yet do FastCGI
"""
# coding=utf-8
import logging
import os
import sys
import argparse
import asyncio

import datetime

import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from aiohttp import web
#from jsonrpcserver.aio import methods
import yo
from yo.api_methods import methods

from yo.storage import init_db
from yo.storage import close_db

from yo.transports import init_transports

from yo.storage import wwwpushsubs

log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'))
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

from yo import static_content

async def handle_api(request):
    req_app = request.app
    request = await request.json()
    logger.debug('Incoming request: %s' % request)
    if not 'params' in request.keys(): request['params'] = {} # fix for API methods that have no params
    request['params']['db'] = req_app['config']['db']
    response = await methods.dispatch(request)
    return web.json_response(response)

async def handle_health(request):
    return web.json_response({'status': 'OK',
                              'datetime': datetime.datetime.utcnow().isoformat()})

async def handle_wwwpush_sub(request):
      req_app = request.app
      request = await request.json()
      logger.debug('Incoming web-push sub: %s' % str(request))
      user_profile = await storage.users.get_by_name(req_app['config']['db'],request['username'])
      if not user_profile:
         logger.error('Did not find user profile for %s' % request['username'])
         return web.json_response({'success':False,'err_msg':'No such user'})
      else:
         logger.debug('Found user profile: %s' % str(user_profile))

      user_sub = {'to_uid':       user_profile['uid'],
                  'push_sub_json':str(request['push_sub'])}

      is_valid = True
      try:
         await storage.wwwpushsubs.put(req_app['config']['db'],user_sub)
      except Exception as e:
         is_valid = False
         logger.exception('Failed to store new sub', e, extra=request)

      if is_valid:
         return web.json_response({'success':True,'user_profile':storage.users.to_json_dict(user_profile)})
      else:
         return web.json_response({'success':False,'err_msg':'Internal error'})

async def handle_fcm_sub(request):
      req_app = request.app
      request = await request.json()
      logger.debug('Incoming android FCM sub: %s' % str(request))

      user_profile = await storage.users.get_by_name(req_app['config']['db'],request['username'])
      if not user_profile:
         logger.error('Did not find user profile for %s' % request['username'])
         return web.json_response({'success':False,'err_msg':'No such user'})
      else:
         logger.debug('Found user profile: %s' % str(user_profile))

      user_sub = {'to_uid':       user_profile['uid'],
                  'push_sub_json':str(request['push_sub'])}

      is_valid = True
      try:
         await storage.android_fcm_subs.put(req_app['config']['db'],user_sub)
      except Exception as e:
         is_valid = False
         logger.exception('Failed to store new sub', e, extra=request)

      if is_valid:  
         return web.json_response({'success':True,'user_profile':storage.users.to_json_dict(user_profile)})
      else:
         return web.json_response({'success':False,'err_msg':'Internal error'})


      return web.json_response({'success':True})

def init(loop, argv):
    parser = argparse.ArgumentParser(description="yo notification server")
    parser.add_argument('--server_port', type=int, default=9000)
    parser.add_argument('--server_host', type=str, default='0.0.0.0')
    parser.add_argument('--database_url', type=str, default='sqlite://')
    args = parser.parse_args(argv)

    # setup application and extensions
    app = web.Application(loop=loop)

    # load config from yaml file in current dir
    app['config'] = {
        'host': args.server_host,
        'port': args.server_port,
        'database_url': args.database_url,
    }

    # create connection to the database
    app.on_startup.append(init_db)
    app.on_startup.append(init_transports)
    # shutdown db connection on exit
    app.on_cleanup.append(close_db)

    # setup routes
    app.router.add_get('/',      handle_health)
    app.router.add_get('/health',handle_health)
    app.router.add_post('/', handle_api)

    # add the static stuff for WWW push demo
    static_content.add_wwwpush_statics(app)

    # TODO - implement a javascript JSON-RPC client and make this an API call
    app.router.add_post('/wwwpush/add_sub', handle_wwwpush_sub)

    # TODO - as above
    app.router.add_post('/android_fcm/add_sub', handle_fcm_sub)


    return app


def main(argv):
    loop = asyncio.get_event_loop()
    app = init(loop, argv)
    web.run_app(app,
                host=app['config']['host'],
                port=app['config']['port'])


if __name__ == '__main__':
    main(sys.argv[1:])
