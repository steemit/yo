# coding=utf-8
import asyncio
import logging

from .base_service import YoBaseService

logger = logging.getLogger(__name__)


class YoAPIServer(YoBaseService):
    service_name = 'api_server'
    q = asyncio.Queue()

    async def api_reset_statuses(self,
                                 username=None,
                                 context=None):
        yo_db = context['yo_db']
        retval = yo_db.wwwpoll_reset_statuses(username)
        return retval

    async def api_get_notifications(self,
                                    username=None,
                                    created_before=None,
                                    updated_after=None,
                                    read=None,
                                    notify_types=None,
                                    limit=30,
                                    test=False,
                                    orig_req=None,
                                    context=None,
                                    **kwargs):
        """ Get all notifications since the specified time

       Keyword args:
          username(str): The username to query for
          created_before(str): ISO8601-formatted timestamp
          updated_after(str): ISO8601-formatted timestamp
          read(bool): If set, only returns notifications with read flag set to this value
          notify_types(str): The notification type to return
          limit(int): The maximum number of notifications to return, defaults to 30
          test(bool): If True, uses mock data only instead of talking to the database backend

       Returns:
          list: list of notifications represented in dictionary format
       """
        yo_db = context['yo_db']
        notifications = yo_db.get_wwwpoll_notifications(
            to_username=username,
            created_before=created_before,
            updated_after=updated_after,
            notify_types=notify_types,
            read=read,
            limit=limit)
        retval = []
        for notification in notifications:
          retval.append(notification)
        return retval

    async def api_mark_read(self,
                            ids=None,
                            orig_req=None,
                            test=False,
                            context=None,
                            **kwargs):
        """ Mark a list of notifications as read

       Keyword args:
           ids(list): List of notifications to mark read

       Returns:
           list: list of notifications updated
       """
        yo_db = context['yo_db']
        ids = ids or []
        rv = []
        for id in ids:
            rv.append(yo_db.wwwpoll_mark_read(id))
        return rv

    async def api_mark_shown(self,
                            ids=None,
                            orig_req=None,
                            context=None,
                            **kwargs):
        """ Mark a list of notifications as shown

       Keyword args:
           ids(list): List of notifications to mark shown

       Returns:
           list: list of notifications updated
       """
        yo_db = context['yo_db']
        ids = ids or []
        rv = []
        for id in ids:
            rv.append(yo_db.wwwpoll_mark_shown(id))
        return rv

    async def api_mark_unread(self,
                              ids=None,
                              orig_req=None,
                              test=False,
                              context=None,
                              **kwargs):
        """ Mark a list of notifications as unread

       Keyword args:
           ids(list): List of notifications to mark unread

       Returns:
           list: list of notifications updated
       """
        yo_db = context['yo_db']
        ids = ids or []
        rv = []
        for id in ids:
            rv.append(yo_db.wwwpoll_mark_unread(id))
        return rv


    async def api_mark_unshown(self,
                              ids=None,
                              orig_req=None,
                              test=False,
                              context=None,
                              **kwargs):
        """ Mark a list of notifications as unshown

       Keyword args:
           ids(list): List of notifications to mark unshown

       Returns:
           list: list of notifications updated
       """
        yo_db = context['yo_db']
        ids = ids or []
        rv = []
        for id in ids:
            rv.append(yo_db.wwwpoll_mark_unshown(id))
        return rv

    async def api_set_transports(self,
                                 username=None,
                                 transports=None,
                                 orig_req=None,
                                 context=None,
                                 **kwargs):
        transports = transports or {}
        # do some quick sanity checks first
        if len(transports.items()) == 0:
            return None  # this should be an error of course
        for k, v in transports.items():
            if len(v.items()) != 2:
                return None  # each transport should only have 2 fields
            if not 'notification_types' in v.keys(): return None
            if not 'sub_data' in v.keys(): return None

        return transports

    async def api_get_transports(self,
                                 username=None,
                                 orig_req=None,
                                 test=False,
                                 context=None,
                                 **kwargs):
        yo_db = context['yo_db']
        return yo_db.get_user_transports(username)


    async def async_task(self, yo_app):  # pragma: no cover
        yo_app.add_api_method(self.api_set_transports, 'set_transports')
        yo_app.add_api_method(self.api_get_transports, 'get_transports')
        yo_app.add_api_method(self.api_get_notifications, 'get_notifications')
        yo_app.add_api_method(self.api_mark_read, 'mark_read')
        yo_app.add_api_method(self.api_mark_shown, 'mark_shown')
        yo_app.add_api_method(self.api_mark_unread, 'mark_unread')
        yo_app.add_api_method(self.api_mark_unshown, 'mark_unshown')
        yo_app.add_api_method(self.api_reset_statuses, 'reset_statuses')

