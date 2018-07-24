#! /usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio

import click
import yo.yolog
import json
import structlog
logger = structlog.get_logger()

def channel_callback(conn,pid,channel,payload):
    logger.info('NOTIFY',conn=conn,pid=pid, channel=channel, payload_type=type(payload), payload=payload)


async def watch_table(database_url, table_name, channel):
    from yo.db import create_asyncpg_conn
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    loop = asyncio.get_event_loop()
    conn = await create_asyncpg_conn(database_url, loop=loop)
    await conn.execute('''select watch_queue_table($1, $2);''', table_name, channel)
    logger.info('added triggers', table=table_name, channel=channel)
    await conn.add_listener(channel, channel_callback)
    logger.info('added listener', table=table_name, channel=channel)
    while True:
        logger.info('listening',table=table_name, channel=channel)
        await asyncio.sleep(60)

@click.command(name='watch-table')
@click.option('--database_url', envvar='DATABASE_URL')
@click.option('--table_name')
@click.option('--channel')
def watch(database_url, table_name, channel):
    loop = asyncio.get_event_loop()
    from yo.db.queue import queue_watcher
    from yo.db.queue import worker_function
    loop.run_until_complete(queue_watcher(database_url=database_url, channel=channel, worker_func=worker_function))



if __name__ == "__main__":
    watch()
