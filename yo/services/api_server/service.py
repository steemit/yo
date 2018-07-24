# -*- coding: utf-8 -*-
import asyncio
import datetime
import functools
import yojson
import os

import structlog
import uvloop
from aiohttp import web
from jsonrpcserver import config
from jsonrpcserver.async_methods import AsyncMethods

import services.api_server.api_methods

from ..base_service import YoBaseService
from .api_methods import api_get_notifications
from .api_methods import api_mark_read
from .api_methods import api_mark_shown
from .api_methods import api_mark_unread
from .api_methods import api_mark_unshown
from .api_methods import api_get_transports
from .api_methods import api_set_transports

config.log_responses = False
config.log_requests = False

logger = structlog.getLogger(__name__, service_name='api_server')


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def default_json(obj):
    if isinstance(obj, datetime.datetime):
        return str(obj)
    raise TypeError('Unable to serialize {!r}'.format(obj))


json_dumps = functools.partial(yojson.dumps, default=default_json)
json_response = functools.partial(web.json_response, dumps=json_dumps)


class YoAPIServer(YoBaseService):
    service_name = 'api_server'
    def __init__(self, database_url=None, loop=None, http_host=None, http_port=None):
        super().__init__(database_url=database_url, loop=loop)
        self.host = http_host
        self.port = http_port

        self.web_app = web.Application(loop=self.loop)
        self.api_methods = AsyncMethods()
        self.web_app.router.add_post('/', self.handle_api)
        self.web_app.router.add_get('/.well-known/healthcheck.json',
                                    self.healthcheck_handler)
        self.web_app.router.add_get('/health', self.healthcheck_handler)
        self.api_methods.add(
            api_get_notifications,
            'yo.get_db_notifications')
        self.api_methods.add(api_mark_read,
                             'yo.mark_read')
        self.api_methods.add(api_mark_unread,
                             'yo.mark_unread')
        self.api_methods.add(api_mark_shown,
                             'yo.mark_shown')
        self.api_methods.add(api_mark_unshown,
                             'yo.mark_unshown')
        self.api_methods.add(api_get_transports,
                             'yo.get_transports')
        self.api_methods.add(api_set_transports,
                             'yo.set_transports')
        self.api_methods.add(self.api_healthcheck, 'health')

    async def healthcheck_handler(self, request):
        return web.json_response(await self.api_healthcheck())

    async def handle_api(self, request):
        request = await request.json()
        context = {'app': self}
        response = await self.api_methods.dispatch(request, context=context)
        return json_response(response)

    @staticmethod
    async def api_healthcheck():
        return {
            'status':        'OK',
            'source_commit': os.environ.get('SOURCE_COMMIT'),
            'docker_tag':    os.environ.get('DOCKER_TAG'),
            'datetime':      datetime.datetime.utcnow().isoformat()
        }

    async def main_task(self):
        web.run_app(self.web_app, host=self.host,port=self.port)

