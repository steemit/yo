# -*- coding: utf-8 -*-
import asyncio
import datetime
import logging
import os

import uvloop
from aiohttp import web
from jsonrpcserver.async_methods import AsyncMethods

logger = logging.getLogger(__name__)

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

ALLOWED_ORIGINS = ['http://localhost:8080', 'https://steemitdev.com']


# pylint: disable=too-many-instance-attributes
class YoApp:
    def __init__(self, config=None, db=None):

        self.config = config
        self.db = db
        self.services = {}
        self.service_tasks = {}
        self.loop = asyncio.get_event_loop()
        self.web_app = web.Application(loop=self.loop)
        self.web_app['config'] = {
            'yo_config': self.config,
            'yo_db': self.db,
            'yo_app': self
        }
        self.api_methods = AsyncMethods()
        self.running = False

    async def handle_api(self, request):
        req_app = request.app
        request = await request.json()
        logger.debug('Incoming request: %s', request)
        if 'params' not in request.keys():
            request['params'] = {}  # fix for API methods that have no params
        context = {'yo_db': req_app['config']['yo_db']}
        response = await self.api_methods.dispatch(request, context=context)
        return web.json_response(response)

    def add_api_method(self, func, func_name):
        logger.debug('Adding API method %s', func_name)
        self.api_methods.add(func, name='yo.%s' % func_name)

    # pylint: disable=unused-argument
    async def start_background_tasks(self, app):
        logger.info('Starting tasks...')
        for k, v in self.service_tasks.items():
            logger.info('Starting %s', k)
            self.web_app['service_task:%s' %
                         k] = self.web_app.loop.create_task(v())

    # pylint: enable=unused-argument

    @staticmethod
    async def api_healthcheck():
        return {
            'status': 'OK',
            'source_commit': os.environ.get('SOURCE_COMMIT'),
            'docker_tag': os.environ.get('DOCKER_TAG'),
            'datetime': datetime.datetime.utcnow().isoformat()
        }

    # pylint: disable=unused-argument
    async def healthcheck_handler(self, request):
        return web.json_response(await self.api_healthcheck())

    # pylint: enable=unused-argument

    @staticmethod
    async def handle_options(request):
        origin = request.headers['Origin']
        if origin in ALLOWED_ORIGINS:
            response = web.Response(
                status=204,
                headers={
                    'Access-Control-Allow-Methods': 'POST',
                    'Access-Control-Allow-Origin': origin,
                    'Access-Control-Allow-Headers': '*'
                })
        else:
            response = web.Response(status=403)
        return response

    # pylint: disable=unused-argument
    async def setup_standard_api(self, app):
        self.add_api_method(self.api_healthcheck, 'healthcheck')
        self.web_app.router.add_post('/', self.handle_api)
        self.web_app.router.add_get('/.well-known/healthcheck.json',
                                    self.healthcheck_handler)

    # pylint: enable=unused-argument

    def run(self):
        self.running = True
        self.web_app.on_startup.append(self.start_background_tasks)
        self.web_app.on_startup.append(self.setup_standard_api)
        web.run_app(
            self.web_app,
            host=self.config.get_listen_host(),
            port=self.config.get_listen_port())

    def add_service(self, service_kls):
        logger.debug('Adding service %s', service_kls)
        service = service_kls(yo_app=self, config=self.config, db=self.db)
        name = service.get_name()
        self.service_tasks[name] = service.async_task
        service.yo_app = self
        self.services[name] = service
        service.init_api()

    async def invoke_private_api(self, service=None, api_method=None,
                                 **kwargs):
        # TODO - add support for URLs other than :local:
        if service not in self.services.keys():
            return {'error': 'No such service found!'}
        if api_method not in self.services[service].private_api_methods.keys():
            return {'error': 'No such method in service'}
        return await self.services[service].private_api_methods[api_method](
            **kwargs)
