""" Maintains in-memory mock notifications
"""

import random
import datetime
import dateutil
import dateutil.parser
import time

ACCOUNT_UPDATE = 'account_update'
ANNOUNCEMENT_IMPORTANT = 'announcement_important'
COMMENT_REPLY = 'comment_reply'
FEED = 'feed'
FOLLOW = 'follow'
MENTION = 'mention'
POST_REPLY = 'post_reply'
POWER_DOWN = 'power_down'
SEND_STEEM = 'send'
RECEIVE_STEEM = 'receive'
RESTEEM = 'resteem'
REWARD = 'reward'
VOTE = 'vote'

authors = ['razu','the-alien', 'dreemit', 'timcliff','abh12345','richq11','larkenrose']
# .id and .created should be auto generated for all.
mockNotificationTemplates = [
    dict(
        read=False,
        shown=False,
        notify_type=POWER_DOWN,
        data=dict(
            author="roadscape",
            amount=10000.2
        )
    ),
    dict(
        read=False,
        shown=False,
        notify_type=ANNOUNCEMENT_IMPORTANT,
        data=dict(
            author="steemit",
            item=dict(
                author="wolfcat",
                category="introduceyourself",
                depth=0,
                permlink="from-the-hills-of-ireland-to-planet-steem-a-wolfy-hello",
                summary="From the Hills of Ireland to Planet Steem, A Wolfy Hello!"
            )

        )
    ),
    dict( #UID1
        read=False,
        shown=False,
        notify_type=RESTEEM,
        data=dict(
            author="roadscape",
            item=dict(
                author="wolfcat",
                category="introduceyourself",
                depth=0,
                permlink="from-the-hills-of-ireland-to-planet-steem-a-wolfy-hello",
                summary="From the Hills of Ireland to Planet Steem, A Wolfy Hello!"
            )

        )
    ),
    dict( #UID2
        read=False,
        shown=False,
        notify_type=VOTE,
        data=dict(
            author="beanz",
            item=dict(
                author="wolfcat",
                category="introduceyourself",
                depth=0,
                permlink="from-the-hills-of-ireland-to-planet-steem-a-wolfy-hello",
                summary="From the Hills of Ireland to Planet Steem, A Wolfy Hello!"
            )

        )
    ),
    dict( #UID3
        read=False,
        shown=False,
        notify_type=RECEIVE_STEEM,
        data=dict(
            author="roadscape",
            amount=10000.3
        )
    ),
    dict( #UID4
        read=False,
        shown=False,
        notify_type=MENTION,
        data=dict(
            author="lovejoy",
            item=dict(
                author="wolfcat",
                category="introduceyourself",
                depth=2,
                permlink="re-steemcleaners-re-steemcleaners-re-wolfcat-from-the-hills-of-ireland-to-planet-steem-a-wolfy-hello-20170919t120245144z",
                summary="@wolfcat is a new user who normally doesn't spend a lot of time online, plus we are ",
                parent_summary="You may want to retract your votes.The account has ignored our many requests to confirm the identity. It seems to be another case of fake identity. Thanks."
            ),
            rootItem=dict(
                author="wolfcat",
                category="introduceyourself",
                depth=0,
                permlink="from-the-hills-of-ireland-to-planet-steem-a-wolfy-hello",
                summary="From the Hills of Ireland to Planet Steem, A Wolfy Hello!"
            )

        )
    ),
    dict( #UID5
        read=False,
        shown=False,
        notify_type=VOTE,
        data=dict(
            author="roadscape",
            item=dict(
                author="wolfcat",
                category="introduceyourself",
                depth=0,
                permlink="from-the-hills-of-ireland-to-planet-steem-a-wolfy-hello",
                summary="From the Hills of Ireland to Planet Steem, A Wolfy Hello!"
            )

        )
    ),
    dict( #UID6
        read=False,
        shown=False,
        notify_type=POST_REPLY,
        data=dict(
            author="lovejoy",
            item=dict(
                author="lovejoy",
                category="introduceyourself",
                depth=2,
                permlink="re-steemcleaners-re-steemcleaners-re-wolfcat-from-the-hills-of-ireland-to-planet-steem-a-wolfy-hello-20170919t120245144z",
                summary="@wolfcat is a new user who normally doesn't spend a lot of time online, plus we are "
            ),
            rootItem=dict(
                author="wolfcat",
                category="introduceyourself",
                permlink="from-the-hills-of-ireland-to-planet-steem-a-wolfy-hello",
                summary="From the Hills of Ireland to Planet Steem, A Wolfy Hello!"
            )

        )
    ),
    dict( #UID7
        read=False,
        shown=False,
        notify_type=COMMENT_REPLY,
        data=dict(
            author="dbzfan4awhile",
            item=dict(
                author="dbzfan4awhile",
                category="introduceyourself",
                depth=3,
                permlink="re-wolfcat-re-dbzfan4awhile-re-wolfcat-from-the-hills-of-ireland-to-planet-steem-a-wolfy-hello-20170918t172118886z",
                summary="Awesome",
                parent_summary="Yes! Ill look for you there :)"
            ),
            rootItem=dict(
                author="wolfcat",
                category="introduceyourself",
                permlink="from-the-hills-of-ireland-to-planet-steem-a-wolfy-hello",
                summary="From the Hills of Ireland to Planet Steem, A Wolfy Hello!"
            )

        )
    ),
]


class YoMockData:
   """ A set of in-memory mock notifications
   """
   def __init__(self):
       self.reset()
   def reset(self):
       """ Reset the current status of the mock notifications
           Also freshly generates a new set of data
       """

       self.notifications_by_id = {}
       #self.add_new_notification(notify_type='power_down',username='test_user',data=dict(amount=6.66),id=61)
       #self.add_new_notification(notify_type='power_up',username='test_user',data=dict(amount=13.37),id=62)
       #self.add_new_notification(notify_type='resteem',username='test_user',data=dict(resteemed_item=dict(author='test_user',category='test',permlink='test-post',summary='A test post',resteemed_by='some_user')),id=63)
       #self.add_new_notification(notify_type='feed',username='test_user',data=dict(item=dict(author='some_user',category='test',permlink='another-test',summary='Stuff etc')),id=64)
       #self.add_new_notification(notify_type='reward',username='test_user',data=dict(reward_type='curation',item=dict(author='test_user',category='test',permlink='test-post',summary='A test post'),
       #                                                                                                     amount=dict(SBD=6.66,SP=13.37)),id=65)


       for x in range(60):
           self.add_new_notification(username='test_user', id=x)
       #    self.add_new_notification(notify_type='vote',username='test_user',data=dict(author=authors[random.randint(0, (len(authors)-1))],weight=100,item=dict(author='test_user',permlink='test-post-%s' % x, summary='A test post',
       #                                                                                                                              category='test',depth=0)),id=x)
   def add_new_notification(self,notify_type=None,created=None,username=None,data={}, id=None):
       notify_id = id

       if id is None:
          notify_id = random.randint(100,9999999)


       if created is None:
           seconds = time.time() - (60 * notify_id)
           created = datetime.datetime.fromtimestamp(seconds).isoformat()
       '''
       if notify_id > 60 and notify_id < 66:
           self.notifications_by_id[notify_id] = {'notify_id':  int(notify_id),
                                              'notify_type': notify_type,
                                              'created':    created,
                                              'updated':    created,
                                              'read':       False,
                                              'seen':       False,
                                              'username':   username,
                                              'data':       data}
           '''

       index = notify_id if notify_id < len(mockNotificationTemplates) else random.randint(0, len(mockNotificationTemplates) -1)
       print("Notification " + str(notify_id) + " " + str(index))
       notif = mockNotificationTemplates[index]
       print(notif)
       self.notifications_by_id[notify_id] = {'notify_id':  int(notify_id),
                                              'notify_type': notif.get('notify_type'),
                                              'created':    created,
                                              'updated':    created,
                                              'read':       notif.get('read'),
                                              'seen':       notif.get('seen'),
                                              'username':   username,
                                              'data':       notif.get('data')}
       print(self.notifications_by_id[notify_id])


   def mark_notification_read(self,notify_id=None):
       self.notifications_by_id[notify_id]['read'] = True
       self.notifications_by_id[notify_id]['updated'] = datetime.datetime.now().isoformat()
   def mark_notification_seen(self,notify_id=None):
       self.notifications_by_id[notify_id]['seen'] = True
       self.notifications_by_id[notify_id]['updated'] = datetime.datetime.now().isoformat()
   def mark_notification_unread(self,notify_id=None):
       self.notifications_by_id[notify_id]['read'] = False
       self.notifications_by_id[notify_id]['updated'] = datetime.datetime.now().isoformat()
   def mark_notification_unseen(self,notify_id=None):
       self.notifications_by_id[notify_id]['seen'] = False
       self.notifications_by_id[notify_id]['updated'] = datetime.datetime.now().isoformat()
   def get_notification(self,notify_id=None):
       """ Return a single notification
           If not found, returns None
       """
       if not notify_id in self.notifications_by_id.keys(): return None
       return self.notifications_by_id[notify_id]
   def get_notifications(self,username=None,created_before=None,updated_after=None,read=None,notify_types=None,limit=30):
       retval = []
       if not (created_before is None):
          created_before_query = dateutil.parser.parse(created_before)
       if not (updated_after is None):
          updated_after_query = dateutil.parser.parse(updated_after)
       for k,v in self.notifications_by_id.items():
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
