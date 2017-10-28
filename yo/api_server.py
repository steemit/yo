# coding=utf-8
import asyncio
import logging

from .base_service import YoBaseService
from .mock_notifications import YoMockData
from .mock_settings import YoMockSettings

logger = logging.getLogger(__name__)


class YoAPIServer(YoBaseService):
    service_name = 'api_server'
    q = asyncio.Queue()

    test_notifications = YoMockData()
    test_settings = YoMockSettings()

    def __init__(self, yo_app, config=None, db=None):
        super().__init__(yo_app=yo_app, config=config, db=db)
        self.testing_allowed = self.yo_app.config.config_data['api_server'].get('allow_testing', False)

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
        if test:
            if self.testing_allowed:
                retval = self.test_notifications.get_notifications(
                        username=username,
                        created_before=created_before,
                        updated_after=updated_after,
                        notify_types=notify_types,
                        read=read)[:limit]
            else:
                return {
                    'error': 'tried to use testing mode in prod'
                }  # TODO - conform to proper error format as per github issue https://github.com/steemit/yo/issues/19
        else:
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
        if ids is None:
            ids = []
        retval = []
        if test and self.testing_allowed:
            for notify_id in ids:
                self.test_notifications.mark_notification_read(notify_id)
                retval.append(
                        self.test_notifications.get_notification(notify_id))
        return retval

    async def api_mark_shown(self,
                             ids=None,
                             orig_req=None,
                             test=False,
                             yo_db=None,
                             **kwargs):
        """ Mark a list of notifications as shown

       Keyword args:
           ids(list): List of notifications to mark shown

       Returns:
           list: list of notifications updated
       """
        if ids is None:
            ids = []
        retval = []
        if test and self.testing_allowed:
            for notify_id in ids:
                self.test_notifications.mark_notification_shown(notify_id)
                retval.append(
                        self.test_notifications.get_notification(notify_id))
        return retval

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
        if ids is None:
            ids = []
        retval = []
        if test and self.testing_allowed:
            for notify_id in ids:
                self.test_notifications.mark_notification_unread(notify_id)
                retval.append(
                        self.test_notifications.get_notification(notify_id))
        return retval

    async def api_mark_unshown(self,
                               ids=None,
                               orig_req=None,
                               test=False,
                               yo_db=None,
                               **kwargs):
        """ Mark a list of notifications as unshown

       Keyword args:
           ids(list): List of notifications to mark unshown

       Returns:
           list: list of notifications updated
       """
        if ids is None:
            ids = []
        retval = []
        if test:
            if self.testing_allowed:
                for notify_id in ids:
                    self.test_notifications.mark_notification_unshown(notify_id)
                    retval.append(
                            self.test_notifications.get_notification(notify_id))
            else:
                return None  # TODO - error here
        else:
            pass  # TODO - real implementation here
        return retval

    async def api_reset_test_data(self, **kwargs):
        # this is required for testing of external apps without messing with real data
        if self.testing_allowed:
            self.test_notifications.reset()
            self.test_settings.reset()

    async def api_set_transports(self,
                                 username=None,
                                 transports=None,
                                 orig_req=None,
                                 test=False,
                                 yo_db=None,
                                 **kwargs):
        # do some quick sanity checks first
        if transports is None:
            transports = {}
        if len(transports.items()) == 0:
            return None  # this should be an error of course
        for k, v in transports.items():
            if len(v.items()) != 2:
                return None  # each transport should only have 2 fields
            if not 'notification_types' in v.keys(): return None
            if not 'sub_data' in v.keys(): return None

        retval = transports
        if test:
            retval = self.test_settings.set_transports(username, transports)
        return retval

    async def api_get_transports(self,
                                 username=None,
                                 orig_req=None,
                                 test=False,
                                 yo_db=None,
                                 **kwargs):
        retval = {}
        if test:
            if self.testing_allowed:
                retval = self.test_settings.get_transports(username)
            else:
                return None  # TODO - return appropriate error here
        else:
            retval = yo_db.get_user_transports(username)
        return retval

    async def async_task(self, yo_app):  # pragma: no cover
        yo_app.add_api_method(self.api_set_transports, 'set_transports')
        yo_app.add_api_method(self.api_get_transports, 'get_transports')
        yo_app.add_api_method(self.api_get_notifications, 'get_notifications')
        yo_app.add_api_method(self.api_reset_test_data, 'reset_test_data')
        yo_app.add_api_method(self.api_mark_read, 'mark_read')
        yo_app.add_api_method(self.api_mark_shown, 'mark_shown')
        yo_app.add_api_method(self.api_mark_unread, 'mark_unread')
        yo_app.add_api_method(self.api_mark_unshown, 'mark_unshown')

