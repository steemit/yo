# -*- coding: utf-8 -*-
import asyncio
import datetime
import functools
import json
import os

from aiohttp import web
from jsonrpcserver import config
from jsonrpcserver.async_methods import AsyncMethods
import structlog
import uvloop

import yo.api_methods

config.log_responses = False
config.log_requests = False

logger = structlog.getLogger(__name__)

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def default_json(obj):
    if isinstance(obj, datetime.datetime):
        return str(obj)
    raise TypeError('Unable to serialize {!r}'.format(obj))


json_dumps = functools.partial(json.dumps, default=default_json)
json_response = functools.partial(web.json_response, dumps=json_dumps)


# pylint: disable=too-many-instance-attributes
class YoApp:
    def __init__(self, config=None, db=None):

        self.config = config
        self.db = db
        self.services = {}
        self.service_tasks = {}
        self.loop = asyncio.get_event_loop()
        self.web_app = web.Application(loop=self.loop)
        self.api_methods = AsyncMethods()
        self.running = False
        self.web_app.router.add_post('/', self.handle_api)
        self.web_app.router.add_get('/.well-known/healthcheck.json',
                                    self.healthcheck_handler)

        self.api_methods.add(yo.api_methods.api_get_notifications,
                             'yo.get_db_notifications')
        self.api_methods.add(yo.api_methods.api_mark_read, 'yo.mark_read')
        self.api_methods.add(yo.api_methods.api_mark_unread, 'yo.mark_unread')
        self.api_methods.add(yo.api_methods.api_mark_shown, 'yo.mark_shown')
        self.api_methods.add(yo.api_methods.api_mark_unshown, 'yo.mark_unshown')
        self.api_methods.add(yo.api_methods.api_get_transports, 'yo.get_transports')
        self.api_methods.add(yo.api_methods.api_set_transports, 'yo.set_transports')
        self.api_methods.add(self.api_healthcheck, 'health')

    async def handle_api(self, request):
        request = await request.json()
        context = {'yo_db': self.db}
        response = await self.api_methods.dispatch(request, context=context)
        return json_response(response)

    # pylint: disable=unused-argument
    async def start_background_tasks(self, app):
        logger.info('starting tasks')
        for k, v in self.service_tasks.items():
            logger.info('starting service task', task=k)
            self.web_app['service_task:%s' % k] = self.web_app.loop.create_task(v())

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

    # pylint: disable=unused-argument
    async def on_cleanup(self, app):
        logger.info('executing on_cleanup signal handler')
        futures = [service.shutdown() for service in self.services.values()]
        await asyncio.gather(*futures)

    # pylint: enable=unused-argument

    def run(self):
        self.running = True
        self.web_app.on_startup.append(self.start_background_tasks)
        self.web_app.on_cleanup.append(self.on_cleanup)

        web.run_app(self.web_app, host=self.config.http_host, port=self.config.http_port)

    def add_service(self, service_kls):
        logger.debug('Adding service', service=service_kls.service_name)
        service = service_kls(yo_app=self, config=self.config, db=self.db)
        name = service.get_name()
        self.services[name] = service
        service.init_api()
