# coding=utf-8
import asyncio
import logging

from .base_service import YoBaseService

logger = logging.getLogger(__name__)


class YoAPIServer(YoBaseService):
    service_name = 'api_server'
    q = asyncio.Queue()



    async def api_get_notifications(self,
                                    username=None,
                                    created_before=None,
                                    updated_after=None,
                                    read=None,
                                    notify_types=None,
                                    limit=30,
                                    test=False,
                                    orig_req=None,
                                    yo_db=None,
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
        retval = yo_db.get_wwwpoll_notifications(
            username=username,
            created_before=created_before,
            updated_after=updated_after,
            notify_types=notify_types,
            read=read,
            limit=limit).fetchall()
        return retval

    async def api_mark_read(self,
                            ids=None,
                            orig_req=None,
                            test=False,
                            yo_db=None,
                            **kwargs):
        """ Mark a list of notifications as read

       Keyword args:
           ids(list): List of notifications to mark read
       
       Returns:
           list: list of notifications updated
       """
        ids = ids or []


    async def api_mark_seen(self,
                            ids=None,
                            orig_req=None,
                            test=False,
                            yo_db=None,
                            **kwargs):
        """ Mark a list of notifications as seen

       Keyword args:
           ids(list): List of notifications to mark seen

       Returns:
           list: list of notifications updated
       """
        ids = ids or []


    async def api_mark_unread(self,
                              ids=None,
                              orig_req=None,
                              test=False,
                              yo_db=None,
                              **kwargs):
        """ Mark a list of notifications as unread

       Keyword args:
           ids(list): List of notifications to mark unread
       
       Returns:
           list: list of notifications updated
       """
        ids = ids or []


    async def api_mark_unseen(self,
                              ids=None,
                              orig_req=None,
                              test=False,
                              yo_db=None,
                              **kwargs):
        """ Mark a list of notifications as unseen

       Keyword args:
           ids(list): List of notifications to mark unseen

       Returns:
           list: list of notifications updated
       """
        ids = ids or []



    async def api_set_transports(self,
                                 username=None,
                                 transports=None,
                                 orig_req=None,
                                 test=False,
                                 yo_db=None,
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
                                 yo_db=None,
                                 **kwargs):
        return yo_db.get_user_transports(username)


    async def async_task(self, yo_app):  # pragma: no cover
        yo_app.add_api_method(self.api_set_transports, 'set_transports')
        yo_app.add_api_method(self.api_get_transports, 'get_transports')
        yo_app.add_api_method(self.api_get_notifications, 'get_notifications')
        yo_app.add_api_method(self.api_mark_read, 'mark_read')
        yo_app.add_api_method(self.api_mark_seen, 'mark_seen')
        yo_app.add_api_method(self.api_mark_unread, 'mark_unread')
        yo_app.add_api_method(self.api_mark_unseen, 'mark_unseen')

