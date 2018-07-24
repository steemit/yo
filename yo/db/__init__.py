import asyncio

import asyncpg
import structlog
import sqlalchemy
import sqlalchemy as sa

import yo.json

from sqlalchemy.engine.url import make_url

logger = structlog.getLogger(__name__)

metadata = sqlalchemy.MetaData()

def init_db(db_url):
    from .notifications import notifications_table
    from .users import user_settings_table
    from .queue import queue
    from .desktop import desktop
    url = make_url(db_url)
    log = logger.bind(db_url=url)
    log.info('initializing database')
    engine = sa.create_engine(db_url)
    metadata.create_all(bind=engine)
    log.info('database initialized')

def reset_db(db_url):
    from .actions import actions_table
    from .notifications import notifications_table
    from .users import user_settings_table
    from .queue import queue
    from .desktop import desktop
    url = make_url(db_url)
    log = logger.bind(db_url=url)
    engine = sa.create_engine(db_url)
    log.info('resetting database',)
    metadata.drop_all(bind=engine)
    log.info('database reset')
    log.info('initializing database')
    metadata.create_all(bind=engine)
    log.info('database initialized')



async def init_conn(conn):
    await conn.set_type_codec(
        'jsonb',
        encoder=yo.json.dumps,
        decoder=yo.json.loads,
        schema='pg_catalog'
    )
    await conn.set_type_codec(
        'json',
        encoder=yo.json.dumps,
        decoder=yo.json.loads,
        schema='pg_catalog'
    )


async def create_asyncpg_pool(database_url,
                              loop=None,
                              max_size=30,
                              **kwargs):
    loop = loop or asyncio.get_event_loop()
    return await asyncpg.create_pool(database_url,
                                     loop=loop,
                                     max_size=max_size,
                                     init=init_conn,
                                     **kwargs)

async def create_asyncpg_conn(database_url,
                              loop=None,
                              max_cached_statement_lifetime=0,
                              max_cacheable_statement_size=0,
                              timeout=60,
                              # FIXME idle_in_transaction_session_timeout (in ms)
                              **kwargs):
    loop = loop or asyncio.get_event_loop()
    conn = await asyncpg.connect(database_url,
                                 loop=loop,
                                 max_cached_statement_lifetime=max_cached_statement_lifetime,
                                 max_cacheable_statement_size=max_cacheable_statement_size,
                                 timeout=timeout,
                                 **kwargs
                                 )
    await conn.set_type_codec(
        'jsonb',
        encoder=yo.json.dumps,
        decoder=yo.json.loads,
        schema='pg_catalog'
    )
    await conn.set_type_codec(
        'json',
        encoder=yo.json.dumps,
        decoder=yo.json.loads,
        schema='pg_catalog'
    )
    return conn
