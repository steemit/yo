# coding=utf-8

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
