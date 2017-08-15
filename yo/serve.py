""" Main entry point for the yo server
    
    As of now does not yet do FastCGI
"""
# coding=utf-8
import logging
import os
import sys
import argparse
import asyncio

import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from aiohttp import web
#from jsonrpcserver.aio import methods
from api_methods import methods

from storage import init_db
from storage import close_db

import storage.wwwpushsubs

log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'))
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)



async def handle_api(request):
    req_app = request.app
    request = await request.json()
    logger.debug('Incoming request: %s' % request)
    if not 'params' in request.keys(): request['params'] = {} # fix for API methods that have no params
    request['params']['db'] = req_app['config']['db']
    response = await methods.dispatch(request)
    return web.json_response(response)

# TODO - move this to somewhere more appropriate and switch to a template engine

gcm_test_content           = ''
gcm_service_worker_content = ''
gcm_js_content             = ''

def init_static_content():
    global gcm_test_content
    global gcm_service_worker_content
    global gcm_js_content
    fd = open('html/gcm_test.html','r')
    gcm_test_content = fd.read()
    fd.close()

    fd = open('js/service_worker.js','r')
    gcm_service_worker_content    = fd.read()
    fd.close()

    fd = open('js/gcm.js','r')
    gcm_js_content = fd.read()
    fd.close()
    
    # the below needs to become a proper template engine
    fd = open('pubkey.txt','r')
    push_pubkey = fd.read()
    fd.close()
    gcm_js_content = gcm_js_content.replace('%%SERVER_KEY%%',push_pubkey)

async def handle_gcm_test(request):
    """ This endpoint is used for simple tests of GCM/Firebase
    """
    return web.Response(body=gcm_test_content,content_type='text/html')

async def handle_gcm_service_worker(request):
    """ This endpoint is the service worker for notifications
    """
    return web.Response(body=gcm_service_worker_content,content_type='text/javascript')

async def handle_gcm_manifest(request):
      return web.json_response({'short_name':'GCM/Firebase test'})

async def handle_gcm_js(request):
      return web.Response(body=gcm_js_content,content_type='text/javascript')

async def handle_gcm_sub(request):
      req_app = request.app
      request = await request.json()
      logger.debug('Incoming web-push sub: %s' % str(request))
      user_profile = await storage.users.get_by_name(req_app['config']['db'],request['username'])
      if not user_profile:
         logger.error('Did not find user profile for %s' % request['username'])
      else:
         logger.debug('Found user profile: %s' % str(user_profile))
      
      return web.json_response({'Success':True,'user_profile':storage.users.to_json_dict(user_profile)})

def init(loop, argv):
    parser = argparse.ArgumentParser(description="yo notification server")
    parser.add_argument('--server_port', type=int, default=8080)
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
    # shutdown db connection on exit
    app.on_cleanup.append(close_db)

    # setup routes
    app.router.add_post('/', handle_api)

    init_static_content()

    # TODO - implement /static or similar instead of this stuff
    app.router.add_get('/gcm',handle_gcm_test)
    app.router.add_get('/gcm/manifest.json',       handle_gcm_manifest)
    app.router.add_get('/gcm/js/service_worker.js',handle_gcm_service_worker)
    app.router.add_get('/gcm/js/gcm.js',           handle_gcm_js)

    # TODO - implement a javascript JSON-RPC client and make this an API call
    app.router.add_post('/gcm/add_sub', handle_gcm_sub)


    return app


def main(argv):
    loop = asyncio.get_event_loop()
    app = init(loop, argv)
    web.run_app(app,
                host=app['config']['host'],
                port=app['config']['port'])


if __name__ == '__main__':
    main(sys.argv[1:])
