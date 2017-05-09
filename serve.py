# coding=utf-8
import logging
import os

from aiohttp import web
from jsonrpcserver.aio import methods


import subscribe as subscriptions


log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'))
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

app = web.Application()


'''

    filter event
    if not event:
        return
    get notification types for event
    if not notification types:
        return
    create notification
    store notification
        if not notification stored:
            error
    if rate_limit_not_exceeded(notification):
        send notification
            if not noticifcation sent:
                error
'''




@methods.add('yo.event')
async def event(event=None):
    '''

    :param event:
    :type event:
    :return:
    :rtype:
    '''
    pass




async def handle(request):
    request = await request.text()
    response = await subscriptions.dispatch(request)
    return web.json_response(response)

app.router.add_post('/', handle)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="yo notification server")
    parser.add_argument('--server_port', type=int, default=8080)
    args = parser.parse_args()
    app['server_port'] = args.server_port

    web.run_app(app, port=args.server_port)