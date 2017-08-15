# coding=utf-8
import logging
import os

import sqlalchemy as sa

import aiomysql.sa

from storage import dbtool

logger = logging.getLogger('__name__')


metadata = sa.MetaData()

from storage import users
from storage import notifications
from storage import wwwpushsubs

async def init_db(app):
    db_url = app['config']['database_url']
    if db_url.startswith('mysql'):
       engine = await aiomysql.sa.create_engine(db_url, loop=app.loop)
    else:
       engine = sa.create_engine(db_url)
    if db_url.startswith('sqlite'):
       users.table.create(engine)
       notifications.table.create(engine)
       wwwpushsubs.table.create(engine)

    app['config']['db'] = engine


async def close_db(app):
    if 'close' in dir(app['config']['db']):
       app['config']['db'].close()
       await app['config']['db'].wait_closed()
