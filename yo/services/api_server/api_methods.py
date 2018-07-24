# -*- coding: utf-8 -*-

import structlog

from ...schema import TransportType
from db.desktop import get__notifications
from db.desktop import mark_read
from db.desktop import mark_unread
from db.desktops import mark_shown
from db.desktop import mark_unshown


logger = structlog.getLogger(__name__)

TRANSPORT_KEYS = {'notification_types', 'sub_data'}
TRANSPORT_TYPES = set(t.value for t in TransportType)


async def api_get_notifications(username=None,
                                created_before=None,
                                updated_after=None,
                                read=None,
                                notify_types=None,
                                limit=30,
                                context=None):
    """ Get all notifications since the specified time

   Keyword args:
      username(str): The username to query for
      created_before(str): ISO8601-formatted timestamp
      updated_after(str): ISO8601-formatted timestamp
      read(bool): If set, only returns notifications with read flag set to this value
      notify_types(str): The notification type to return
      limit(int): The maximum number of notifications to return, defaults to 30

   Returns:
      list: list of notifications represented in dictionary format
   """
    engine = context['app'].async_db_engine
    async with engine.acquire() as conn:
        result = get_wwwpoll_notifications(conn,
            to_username=username,
            created_before=created_before,
            updated_after=updated_after,
            notify_types=notify_types,
            read=read,
            limit=limit)
    return result
# pylint: enable=too-many-arguments

async def api_mark_read(ids=None, context=None):
    """ Mark a list of notifications as read

   Keyword args:
       ids(list): List of notifications to mark read

   Returns:
       list: list of notifications updated
   """
    engine = context['app'].async_db_engine
    async with engine.acquire() as conn:
        ids = ids or []
        return [wwwpoll_mark_read(conn, nid) for nid in ids]


async def api_mark_unread(ids=None, context=None):
    """ Mark a list of notifications as unread

   Keyword args:
       ids(list): List of notifications to mark unread

   Returns:
       list: list of notifications updated
   """
    engine = context['app'].async_db_engine
    async with engine.acquire() as conn:
        ids = ids or []
        return [wwwpoll_mark_unread(conn,nid) for nid in ids]


async def api_mark_shown(ids=None, context=None):
    """ Mark a list of notifications as shown

   Keyword args:
       ids(list): List of notifications to mark shown

   Returns:
       list: list of notifications updated
   """
    engine = context['app'].async_db_engine
    async with engine.acquire() as conn:
        return [wwwpoll_mark_shown(conn,nid) for nid in ids]


async def api_mark_unshown(ids=None, context=None):
    """ Mark a list of notifications as unshown

   Keyword args:
       ids(list): List of notifications to mark unshown

   Returns:
       list: list of notifications updated
   """
    engine = context['app'].async_db_engine
    async with engine.acquire() as conn:
        ids = ids or []
        return [wwwpoll_mark_unshown(conn,nid) for nid in ids]


async def api_get_transports(username=None, context=None):
    Users = context['app'].Users
    return Users[username]


async def api_set_transports(username=None, transports=None, context=None):
    transports = transports or {}

    assert TRANSPORT_TYPES.issuperset(transports.keys()), 'bad transport types'

    for transport in transports.values():
        assert TRANSPORT_KEYS.issuperset(transport.keys()), 'bad transport data'

    Users = context['app'].Users
    Users[username] = transports


def init_api(self):
    self.yo_app.api_methods.add(self.api_get_notifications, 'yo.get_db_notifications')
    self.yo_app.api_methods.add(self.api_mark_read, 'yo.mark_read')
    self.yo_app.api_methods.add(self.api_mark_unread, 'yo.mark_unread')
    self.yo_app.api_methods.add(self.api_mark_shown, 'yo.mark_shown')
    self.yo_app.api_methods.add(self.api_mark_unshown, 'yo.mark_unshown')
    self.yo_app.api_methods.add(self.api_get_transports, 'yo.get_transports')
    self.yo_app.api_methods.add(self.api_set_transports, 'yo.set_transports')
