# -*- coding: utf-8 -*-

import structlog

from .db import TRANSPORT_TYPES as DB_TRANSPORT_TYPES

logger = structlog.getLogger(__name__)

TRANSPORT_KEYS = {'notification_types', 'sub_data'}
TRANSPORT_TYPES = set(DB_TRANSPORT_TYPES)


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
    yo_db = context['yo_db']
    result = yo_db.get_wwwpoll_notifications(
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
    yo_db = context['yo_db']
    ids = ids or []
    return [yo_db.wwwpoll_mark_read(nid) for nid in ids]


async def api_mark_unread(ids=None, context=None):
    """ Mark a list of notifications as unread

   Keyword args:
       ids(list): List of notifications to mark unread

   Returns:
       list: list of notifications updated
   """
    yo_db = context['yo_db']
    ids = ids or []
    return [yo_db.wwwpoll_mark_unread(nid) for nid in ids]


async def api_mark_shown(ids=None, context=None):
    """ Mark a list of notifications as shown

   Keyword args:
       ids(list): List of notifications to mark shown

   Returns:
       list: list of notifications updated
   """
    yo_db = context['yo_db']
    return [yo_db.wwwpoll_mark_shown(nid) for nid in ids]


async def api_mark_unshown(ids=None, context=None):
    """ Mark a list of notifications as unshown

   Keyword args:
       ids(list): List of notifications to mark unshown

   Returns:
       list: list of notifications updated
   """
    yo_db = context['yo_db']
    ids = ids or []
    return [yo_db.wwwpoll_mark_unshown(nid) for nid in ids]


async def api_get_transports(username=None, context=None):
    yo_db = context['yo_db']
    return yo_db.get_user_transports(username)


async def api_set_transports(username=None, transports=None, context=None):
    transports = transports or {}

    assert TRANSPORT_TYPES.issuperset(transports.keys()), 'bad transport types'

    for transport in transports.values():
        assert TRANSPORT_KEYS.issuperset(transport.keys()), 'bad transport data'

    yo_db = context['yo_db']
    return yo_db.set_user_transports(username, transports)


def init_api(self):
    self.yo_app.api_methods.add(self.api_get_notifications, 'yo.get_db_notifications')
    self.yo_app.api_methods.add(self.api_mark_read, 'yo.mark_read')
    self.yo_app.api_methods.add(self.api_mark_unread, 'yo.mark_unread')
    self.yo_app.api_methods.add(self.api_mark_shown, 'yo.mark_shown')
    self.yo_app.api_methods.add(self.api_mark_unshown, 'yo.mark_unshown')
    self.yo_app.api_methods.add(self.api_get_transports, 'yo.get_transports')
    self.yo_app.api_methods.add(self.api_set_transports, 'yo.set_transports')
