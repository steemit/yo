# -*- coding: utf-8 -*-
import asyncio
import time

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import CancelledError
from collections import defaultdict
from functools import partial

import steem
from steem.blockchain import Blockchain

import structlog
import uvloop

from funcy import flatten

from ...db.notifications import create_notification
from ...db import create_asyncpg_pool

from .handlers import handle_vote
from .handlers import handle_account_update
from .handlers import handle_send
from .handlers import handle_receive
from .handlers import handle_follow
from .handlers import handle_resteem
from .handlers import handle_power_down
from .handlers import handle_mention
from .handlers import handle_comment

logger = structlog.getLogger(__name__,service_name='blockchain_follower')
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
logger = logger.bind()
EXECUTOR = ThreadPoolExecutor()

'''
{
            "block": 20000000,
            "op": [
                "author_reward",
                {
                    "author": "ivelina89",
                    "permlink": "friends-forever",
                    "sbd_payout": "2.865 SBD",
                    "steem_payout": "0.000 STEEM",
                    "vesting_payout": "1365.457442 VESTS"
                }
            ],
            "op_in_trx": 0,
            "timestamp": "2018-02-19T07:16:54",
            "trx_id": "0000000000000000000000000000000000000000",
            "trx_in_block": 4294967295,
            "virtual_op": 12
}

'''

op_map = defaultdict(list)
op_map.update({
            'vote': [handle_vote],
            'account_update': [handle_account_update],
            'transfer': [handle_send, handle_receive],
            'custom_json': [handle_follow, handle_resteem],
            'withdraw_vesting': [handle_power_down],
            'comment': [handle_mention, handle_comment]
})


async def execute_sync(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    try:
        part_func = partial(func, *args, **kwargs)
        return await loop.run_in_executor(EXECUTOR, part_func)
    except CancelledError:
        logger.debug('ignoring CancelledError')

def get_start_block(start_block:int = None, blockchain: Blockchain=None):
    start_block = None
    try:
        if isinstance(start_block, int) and start_block < 0:
            start_block = blockchain.get_current_block_num() - start_block
    except Exception:
        logger.exception('service error')
        start_block = None
    logger.debug('get_start_block', start_block=start_block)
    return start_block

async def store_notifications(notifications, pool) -> bool:
    logger.debug('store_notifications', notifications=list(notifications))
    futures = [create_notification(pool, **notification) for notification in notifications]
    result = await asyncio.gather(*futures)
    logger.debug('store_notifications', result=result)
    return True

def gather_notifications(blockchain_op:dict = None) -> list:
    """ Handle notification for a particular op
    """
    op_type = blockchain_op['op'][0]
    if op_type not in op_map:
        logger.debug('skipping operation', op_type=op_type)
        return []

    return [handler(blockchain_op) for handler in op_map[op_type]]

async def ops_iter(blockchain:Blockchain=None, start_block:int=None):
    ops_func = blockchain.stream_from(
        start_block=start_block, batch_operations=False)
    loop_elapsed = 0
    while True:
        logger.debug('new op', interval=loop_elapsed)
        loop_start = time.perf_counter()
        ops = await execute_sync(next, ops_func)
        yield ops
        loop_elapsed = time.perf_counter() - loop_start


async def _main_task(database_url=None, loop=None, steemd_url=None, start_block=None):
    logger.debug('main task starting')
    loop = loop or asyncio.get_event_loop()
    steemd = steem.steemd.Steemd(nodes=[steemd_url])
    blockchain = Blockchain(steemd_instance=steemd)
    pool = await create_asyncpg_pool(database_url=database_url, loop=loop)

    last_block_num_handled = None

    loop_elapsed= 0
    async for op in ops_iter(blockchain, start_block):
        loop_start = time.perf_counter()
        logger.debug('main task', loop_elapsed=loop_elapsed,  op=op)
        block_num = op['block']
        unstored_notifications = list(flatten(gather_notifications(op)))
        logger.debug(
            'main_task',
            block_num=block_num,
            unstored_count=len(unstored_notifications)
        )
        resp = await store_notifications(unstored_notifications, pool)
        if resp:
            last_block_num_handled = block_num
        loop_elapsed = time.perf_counter() - loop_start

def main_task(database_url=None, steemd_url=None, start_block=None):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main_task(
        database_url=database_url,
        loop=loop,
        steemd_url=steemd_url,
        start_block=start_block))
