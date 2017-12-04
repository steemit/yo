# -*- coding: utf-8 -*-
import asyncio
import datetime
import os

from aiohttp import web
from jsonrpcserver.async_methods import AsyncMethods
import structlog
import uvloop

logger = structlog.getLogger(__name__)

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
        logger.debug('incoming request', request=request)
        if 'params' not in request.keys():
            request['params'] = {}  # fix for API methods that have no params
        context = {'yo_db': req_app['config']['yo_db']}
        response = await self.api_methods.dispatch(request, context=context)
        return web.json_response(response)

    def add_api_method(self, func, func_name):
        logger.debug('Adding API method', name=func_name)
        self.api_methods.add(func, name='yo.%s' % func_name)

    # pylint: disable=unused-argument
    async def start_background_tasks(self, app):
        logger.info('starting tasks')
        for k, v in self.service_tasks.items():
            logger.info('starting service task', task=k)
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

    async def on_cleanup(self, app):
        logger.info('executing on_cleanup signal handler')
        futures = [service.shutdown() for service in self.services.values()]

        await asyncio.gather(*futures)

    # pylint: enable=unused-argument

    def run(self):
        self.running = True
        self.web_app.on_startup.append(self.start_background_tasks)
        self.web_app.on_startup.append(self.setup_standard_api)
        self.web_app.on_cleanup.append(self.on_cleanup)

        web.run_app(
            self.web_app,
            host=self.config.get_listen_host(),
            port=self.config.get_listen_port())

    def add_service(self, service_kls):
        logger.debug('Adding service', service=service_kls.service_name)
        service = service_kls(yo_app=self, config=self.config, db=self.db)
        name = service.get_name()
        self.services[name] = service
        service.init_api()
