# coding=utf-8
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

def default_json(obj):
    if isinstance(obj, datetime.datetime):
        return str(obj)
    raise TypeError('Unable to serialize {!r}'.format(obj))


json_dumps = functools.partial(yojson.dumps, default=default_json)
json_response = functools.partial(web.json_response, dumps=json_dumps)


# pylint: disable=unused-argument
async def healthcheck_handler(request):
    return web.json_response(await api_healthcheck())

async def handle_api(request):
    request = await request.json()
    context = {'app': self}
    response = await api_methods.dispatch(request, context=context)
    return json_response(response)


async def api_healthcheck():
    return {
        'status':        'OK',
        'source_commit': os.environ.get('SOURCE_COMMIT'),
        'docker_tag':    os.environ.get('DOCKER_TAG'),
        'datetime':      datetime.datetime.utcnow().isoformat()
    }


