# -*- coding: utf-8 -*-
import asyncio
import time

import uvloop
import structlog


from ...db import create_asyncpg_pool
from ...db.queue import QItem
from ...db.desktop import create_desktop_notification
from ...schema import TransportType

from ...db.users import get_user_email
from ...db.users import get_user_phone
from ...db.actions import get_rates
from ...db.actions import sent


logger = structlog.getLogger(__name__, service_name='notification_sender')
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def send_sms(notification):
    asyncio.sleep(1)

async def send_email(notification):
    asyncio.sleep(1)

async def handle_desktop_transport(pool):
    conn = await pool.acquire()

    while True:
        loop_start = time.perf_counter()
        # begin transaction
        transport_type = TransportType['desktop']
        async with QItem(conn, transport_type=transport_type) as item:
            logger.debug('qitem received', item_str=item)
            time_to_acquire_item = time.perf_counter() - loop_start

            dnid = await create_desktop_notification(conn,
                                                     item['eid'],
                                                     notify_type=item['notify_type'],
                                                     to_username=item['to_username'],
                                                     from_username=item['from_username'],
                                                     json_data=item['json_data']
                                                     )

            time_to_store = time.perf_counter() - time_to_acquire_item
            await sent(conn, item['nid'], item['to_username'], transport_type)
            time_to_mark_sent = time.perf_counter() - time_to_store

        logger.debug('desktop notification processed',
                     dnid=dnid,
                     acquire_item=time_to_acquire_item,
                     store_item=time_to_store,
                     make_sent=time_to_mark_sent,
                     loop_total=time.perf_counter() - loop_start)

async def handle_sms_transport(pool):
    conn = await pool.acquire()
    while True:
        loop_start = time.perf_counter()
        # begin transaction

        transport_type = TransportType['sms']
        loop_start = time.perf_counter()
        # begin transaction
        async with QItem(conn, transport_type=transport_type) as item:
            logger.debug('qitem received', item_str=item)
            time_to_acquire_item = time.perf_counter() - loop_start
            rates = await get_rates(conn, item['to_username'], transport_type)
            if rates or True:
                user_phone = await get_user_email(item['to_username'])
                result = await send_sms(item, user_phone)
                time_to_send = time.perf_counter() - time_to_acquire_item
                await sent(conn, item['nid'], item['to_username'], transport_type.value)
                time_to_mark_sent = time.perf_counter() - time_to_send
            else:
                time_to_send = 0
                time_to_mark_sent = 0

        logger.debug('sms notification processed',
                     acquire_item=time_to_acquire_item,
                     send_item=time_to_send,
                     mark_sent=time_to_mark_sent,
                     loop_total=time.perf_counter() - loop_start)

async def handle_email_transport(pool):
    conn = await pool.acquire()
    while True:
        loop_start = time.perf_counter()
        # begin transaction
        transport_type = TransportType['email']
        loop_start = time.perf_counter()
        # begin transaction
        async with QItem(conn, transport_type=transport_type) as item:
            logger.debug('qitem received', item_str=item)
            time_to_acquire_item = time.perf_counter() - loop_start
            rates = await get_rates(conn, item['to_username'],transport_type)
            if rates or True:
                user_email = await get_user_email(item['to_username'])
                result = await send_email(item, user_email)
                time_to_send = time.perf_counter() - time_to_acquire_item
                await sent(conn, item['nid'], item['to_username'], transport_type.value)
                time_to_mark_sent = time.perf_counter() - time_to_send
            else:
                time_to_send = 0
                time_to_mark_sent = 0

        logger.debug('email notification processed',
                     acquire_item=time_to_acquire_item,
                     send_item=time_to_send,
                     mark_sent=time_to_mark_sent,
                     loop_total=time.perf_counter() - loop_start)




async def _main_task(database_url=None, loop=None):
    logger.debug('main task starting')
    loop = loop or asyncio.get_event_loop()
    pool = await create_asyncpg_pool(database_url=database_url, loop=loop)
    transports = [handle_desktop_transport(pool),
                  #handle_email_transport(pool),
                  #handle_sms_transport(pool),
                  handle_desktop_transport(pool),
                  handle_desktop_transport(pool),
                  handle_desktop_transport(pool),
                  #handle_email_transport(pool),
                  #handle_sms_transport(pool)
                  ]
    await handle_desktop_transport(pool) #asyncio.gather(*transports)




def main_task(database_url=None):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main_task(
        database_url=database_url,
        loop=loop))
