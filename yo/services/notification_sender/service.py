# -*- coding: utf-8 -*-
import asyncio


import uvloop
import structlog


from ...db import create_asyncpg_pool

logger = structlog.getLogger(__name__, service_name='notification_sender')

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

async def _main_task(database_url:str=None, loop=None):
    logger.debug('main task starting')
    loop = loop or asyncio.get_event_loop()
    pool = await create_asyncpg_pool(database_url=database_url, loop=loop)
    # FIXME




def main_task(database_url:str=None):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main_task(
        database_url=database_url,
        loop=loop))
