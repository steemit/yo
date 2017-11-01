# coding=utf-8
""" Maintains in-memory mock notifications
"""

import random
import string
import datetime
import dateutil
import dateutil.parser


class YoMockData:
    """ A set of in-memory mock notifications
   """

    def __init__(self, datetime_as_string=False):
        self.datetime_as_string = datetime_as_string
        self.notifications_by_id = {}
        self.reset()

    def reset(self):
        """ Reset the current status of the mock notifications
           Also freshly generates a new set of data
       """
        authors = [
            'razu', 'the-alien', 'dreemit', 'timcliff', 'abh12345', 'richq11',
            'larkenrose '
        ]
        self.add_new_notification(
                notify_type='power_down',
                username='test_user',
                data=dict(amount=6.66))
        self.add_new_notification(
                notify_type='power_up',
                username='test_user',
                data=dict(amount=13.37))
        self.add_new_notification(
                notify_type='resteem',
                username='test_user',
                data=dict(resteemed_item=dict(
                        author='test_user',
                        category='test',
                        permlink='test-post',
                        summary='A test post',
                        resteemed_by='some_user')),
                id=163)
        self.add_new_notification(
                notify_type='feed',
                username='test_user',
                data=dict(item=dict(
                        author='some_user',
                        category='test',
                        permlink='another-test',
                        summary='Stuff etc')),
                id=164)
        self.add_new_notification(
                notify_type='reward',
                username='test_user',
                data=dict(
                        reward_type='curation',
                        item=dict(
                                author='test_user',
                                category='test',
                                permlink='test-post',
                                summary='A test post'),
                        amount=dict(SBD=6.66, SP=13.37)),
                id=165)

        for x in range(60):
            self.add_new_notification(
                    notify_type='vote',
                    username='test_user',
                    data=dict(
                            author=authors[
                                random.randint(0, (len(authors) - 1))],
                            weight=100,
                            item=dict(
                                    author='test_user',
                                    permlink='test-post-%s' % x,
                                    summary='A test post',
                                    category='test',
                                    depth=0)),
                    id=x)

    def add_new_notification(self,
                             notify_type=None,
                             created=None,
                             username=None,
                             data=None,
                             id=None):
        if data is None:
            data = {}
        notify_id = id

        if id is None:
            notify_id = random.randint(1, 9999999)

        if created is None:
            if self.datetime_as_string is True:
                created = datetime.datetime.utcnow().isoformat()
            else:
                created = datetime.datetime.utcnow()
        self.notifications_by_id[notify_id] = {
            'notify_id':   int(notify_id),
            'notify_type': notify_type,
            'trx_id:':     ''.join(random.choices(string.ascii_uppercase + string.digits, k=15)),
            'created':     created,
            'updated':     created,
            'read':        False,
            'shown':       False,
            'username':    username,
            'data':        data
        }

    def mark_notification_read(self, notify_id=None):
        self.notifications_by_id[notify_id]['read'] = True
        self.notifications_by_id[notify_id][
            'updated'] = datetime.datetime.now().isoformat()

    def mark_notification_shown(self, notify_id=None):
        self.notifications_by_id[notify_id]['shown'] = True
        self.notifications_by_id[notify_id][
            'updated'] = datetime.datetime.now().isoformat()

    def mark_notification_unread(self, notify_id=None):
        self.notifications_by_id[notify_id]['read'] = False
        self.notifications_by_id[notify_id][
            'updated'] = datetime.datetime.now().isoformat()

    def mark_notification_unshown(self, notify_id=None):
        self.notifications_by_id[notify_id]['shown'] = False
        self.notifications_by_id[notify_id][
            'updated'] = datetime.datetime.now().isoformat()

    def get_notification(self, notify_id=None):
        """ Return a single notification
           If not found, returns None
       """
        if not notify_id in self.notifications_by_id.keys(): return None
        return self.notifications_by_id[notify_id]

    def get_notifications(self,
                          username=None,
                          created_before=None,
                          updated_after=None,
                          read=None,
                          notify_types=None,
                          limit=30):
        retval = []
        if not (created_before is None):
            created_before_query = dateutil.parser.parse(created_before)
        if not (updated_after is None):
            updated_after_query = dateutil.parser.parse(updated_after)
        for k, v in self.notifications_by_id.items():
            if not (username is None):
                if v['username'] != username: continue
            if not (created_before is None):
                created_curval = dateutil.parser.parse(v['created'])
                if created_curval >= created_before_query: continue
            if not (updated_after is None):
                updated_curval = dateutil.parser.parse(v['updated'])
                if updated_curval <= updated_after_query: continue
            if not (read is None):
                if v['read'] != read: continue
            if not (notify_types is None):
                if v['notify_type'] not in notify_types: continue
            retval.append(v)
        return retval[:limit]
