# coding=utf-8
import logging
import os

from .dbtool import acquire_db_conn


import sqlalchemy as sa
from sqlalchemy.sql import func

from yo.storage import metadata

logger = logging.getLogger('__name__')

table = sa.Table('yo_email_subs', metadata,
   sa.Column('id', sa.Integer, primary_key=True),
   sa.Column('to_uid', sa.Integer, sa.ForeignKey('yo_users.uid'), nullable=False, index=True),

   sa.Column('email', sa.Unicode, nullable=False, index=False),

   sa.Column('created_at', sa.DateTime, default=func.now()),
   sa.Column('updated_at', sa.DateTime, onupdate=func.now(),default=func.now())
)

# TODO - move the below into a base class or something

async def put(engine, email_sub):
      with acquire_db_conn(engine) as conn:
           return conn.execute(table.insert(), **email_sub)

async def get_by_to_uid(engine, user_id):
      with acquire_db_conn(engine) as conn:
           query = table.select().where(table.c.to_uid == user_id)
           return conn.execute(query).fetchall()

