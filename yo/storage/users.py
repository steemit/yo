# coding=utf-8
import logging
import os

from storage.dbtool import acquire_db_conn


import sqlalchemy as sa
from sqlalchemy.sql import func

from storage import metadata

logger = logging.getLogger('__name__')

table = sa.Table('yo_users', metadata,
   sa.Column('uid', sa.Integer, primary_key=True),  # uid in condensor model
   sa.Column('name', sa.Unicode, nullable=False, index=True, unique=True),  # account name, e.g., 'ned'
   sa.Column('email', sa.Unicode, nullable=False, index=True, unique=True),
   sa.Column('first_name', sa.Unicode),
   sa.Column('last_name', sa.Unicode),
   sa.Column('phone', sa.String, nullable=False, index=True),

   sa.Column('created_at', sa.DateTime, default=func.now()),
   sa.Column('updated_at', sa.DateTime, onupdate=func.now())
)


# TODO - need to look at how this works with the MySQL engine, should probably abstract it too
#        perhaps simply make a generic function for acquiring connection from underlying DB and doing stuff with it in a python3 context

async def put(engine, user):
      with acquire_db_conn(engine) as conn:
           return conn.execute(table.insert(), **user)

async def get(engine, user_id):
      with acquire_db_conn(engine) as conn:
           query = table.select().where(table.c.uid == user_id)
           return query.execute().first()

async def get_by_name(engine, user_name):
      with acquire_db_conn(engine) as conn:
           query = table.select().where(table.c.name == user_name)
           return query.execute().first()

async def get_by_email(engine, email):
    async with engine.connect() as conn:
        query = table.select().where(table.c.email == email)
        return await query.execute().first()


async def get_by_phone(engine, phone):
    async with engine.connect() as conn:
        query = table.select().where(table.c.phone == phone)
        return await query.execute().first()

async def update(engine, user):
    async with engine.connect() as conn:
        return await conn.execute(table.update(), **user)

