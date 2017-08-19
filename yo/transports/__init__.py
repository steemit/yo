# coding=utf-8
import logging
import os
import asyncio
import json

from .wwwpush import WWWPushTransport
from .sendgrid import SendgridEmailTransport

# TODO - add config and better key management
active_transports = {}

async def init_transports(app):
    active_transports['browser'] = WWWPushTransport(db=app['config']['db'])
    active_transports['email']   = SendgridEmailTransport(db=app['config']['db'])


async def send(notification):
    transport = notification['transport']
    if transport in active_transports.keys():
       active_transports[transport].send_notification(notification['to'],
                                                      notify_type = notification['type'],
                                                      data        = json.loads(notification['source_event']),
                                                      msg_summary = str(notification['data']))
    else:
       raise ValueError('Bad transport %s', transport)
