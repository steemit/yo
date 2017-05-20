# coding=utf-8
import logging
import os

import sqlalchemy as sa

import aiomysql.sa

logger = logging.getLogger('__name__')


metadata = sa.MetaData()


async def init_db(app):
    db_url = app['config']['database_url']
    engine = await aiomysql.sa.create_engine(db_url, loop=app.loop)
    app['config']['db'] = engine


async def close_db(app):
    app['config']['db'].close()
    await app['config']['db'].wait_closed()