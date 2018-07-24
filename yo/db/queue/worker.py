#! /usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio

import click
import yo.yolog
import json
import structlog
logger = structlog.get_logger('worker.cli')



async def worker_funcy(qitem, local_logger, **kwargs):
    local_logger.debug('worker_func qitem', worker_func_qitem=qitem)
    await asyncio.sleep(1)

@click.command(name='work')
@click.option('--database_url', envvar='DATABASE_URL')
def work(database_url):
    loop = asyncio.get_event_loop()
    from yo.db.queue import worker_factory
    q_workers = []
    for i in range(50):
        worker = worker_factory(database_url=database_url,
                              q_visibility_timeout=5,
                              worker_func=worker_funcy)
        q_workers.append(worker())

    loop.run_until_complete(asyncio.gather(*q_workers))



if __name__ == "__main__":
    work()
