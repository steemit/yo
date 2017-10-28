from .base_service import YoBaseService
from .mock_notifications import YoMockData
from .mock_settings import YoMockSettings
from .utils import needs_auth
import asyncio
import json
import steem
import hashlib
from steem.account import Account
import json
import datetime

import logging
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
                            ids=[],
                            orig_req=None,
                            yo_db=None,
                            **kwargs):
        """ Mark a list of notifications as read

       Keyword args:
           ids(list): List of notifications to mark read
       
       Returns:
           list: list of notifications updated
       """
        return None # TODO - replace with real DB lookup

    async def api_mark_seen(self,
                            ids=[],
                            orig_req=None,
                            yo_db=None,
                            **kwargs):
        """ Mark a list of notifications as seen

       Keyword args:
           ids(list): List of notifications to mark seen

       Returns:
           list: list of notifications updated
       """
        return None
    async def api_mark_unread(self,
                              ids=[],
                              orig_req=None,
                              yo_db=None,
                              **kwargs):
        """ Mark a list of notifications as unread

       Keyword args:
           ids(list): List of notifications to mark unread
       
       Returns:
           list: list of notifications updated
       """
        return None

    async def api_mark_unseen(self,
                              ids=[],
                              orig_req=None,
                              yo_db=None,
                              **kwargs):
        """ Mark a list of notifications as unseen

       Keyword args:
           ids(list): List of notifications to mark unseen

       Returns:
           list: list of notifications updated
       """
        return None


    async def api_set_transports(self,
                                 username=None,
                                 transports={},
                                 orig_req=None,
                                 yo_db=None,
                                 **kwargs):
        # do some quick sanity checks first
        if len(transports.items()) == 0:
            return None  # this should be an error of course
        for k, v in transports.items():
            if len(v.items()) != 2:
                return None  # each transport should only have 2 fields
            if not 'notification_types' in v.keys(): return None # TODO - update all these return None bits with proper errors
            if not 'sub_data' in v.keys(): return None
        return yo_db.set_user_transports(username,transports)

    async def api_get_transports(self,
                                 username=None,
                                 orig_req=None,
                                 yo_db=None,
                                 **kwargs):
        retval = yo_db.get_user_transports(username)
        return retval

    async def async_task(self, yo_app):  # pragma: no cover
        yo_app.add_api_method(self.api_set_transports, 'set_transports')
        yo_app.add_api_method(self.api_get_transports, 'get_transports')
        yo_app.add_api_method(self.api_get_notifications, 'get_notifications')
        yo_app.add_api_method(self.api_mark_read, 'mark_read')
        yo_app.add_api_method(self.api_mark_seen, 'mark_seen')
        yo_app.add_api_method(self.api_mark_unread, 'mark_unread')
        yo_app.add_api_method(self.api_mark_unseen, 'mark_unseen')
