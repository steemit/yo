# coding=utf-8
import logging
import os
import asyncio



async def send(notification):
    transport = notification['transport']
    if transport == 'browser':
        pass
    elif transport == 'sms':
        pass
    elif transport == 'email':
        pass
    elif transport == 'web':
        pass
    else:
        raise ValueError('Bad transport %s', transport)
