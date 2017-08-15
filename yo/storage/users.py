# coding=utf-8
import logging
import os

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

   sa.Column('created_at', sa.DateTime, default=func.utc_timestamp()),
   sa.Column('updated_at', sa.DateTime, onupdate=func.utc_timestamp())
)

async def put(engine, user):
    async with engine.acquire() as conn:
        return await conn.execute(table.insert(), **user)


async def get(engine, user_id):
    async with engine.acquire() as conn:
        query = table.select().where(table.c.uid == user_id)
        return await query.execute().first()


async def get_by_email(engine, email):
    async with engine.acquire() as conn:
        query = table.select().where(table.c.email == email)
        return await query.execute().first()


async def get_by_phone(engine, phone):
    async with engine.acquire() as conn:
        query = table.select().where(table.c.phone == phone)
        return await query.execute().first()


async def get_by_account(engine, account):
    async with engine.acquire() as conn:
        query = table.select().where(table.c.name == account)
        return await query.execute().first()


async def update(engine, user):
    async with engine.acquire() as conn:
        return await conn.execute(table.update(), **user)

