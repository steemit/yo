""" Maintains in-memory mock notifications
"""

import random
import datetime
import dateutil

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
       self.add_new_notification(notify_type='power_down',username='test_user',data=dict(amount=6.66),id=161)
       self.add_new_notification(notify_type='power_up',username='test_user',data=dict(amount=13.37),id=162)
       self.add_new_notification(notify_type='resteem',username='test_user',data=dict(resteemed_item=dict(author='test_user',category='test',permlink='test-post',summary='A test post',resteemed_by='some_user')),id=163)
       self.add_new_notification(notify_type='feed',username='test_user',data=dict(item=dict(author='some_user',category='test',permlink='another-test',summary='Stuff etc')),id=164)
       self.add_new_notification(notify_type='reward',username='test_user',data=dict(reward_type='curation',item=dict(author='test_user',category='test',permlink='test-post',summary='A test post'),
                                                                                                            amount=dict(SBD=6.66,SP=13.37)),id=165)
       for x in range(60):
           self.add_new_notification(notify_type='vote',username='test_user',data=dict(author='some_other_user',weight=100,item=dict(author='test_user',permlink='test-post-%s' % x, summary='A test post',
                                                                                                                                     category='test',depth=0)),id=x)
   def add_new_notification(self,notify_type=None,created=None,username=None,data={}, id=None):
       notify_id = id

       if id is None:
          notify_id = random.randint(1,9999999)


       if created is None:
          created = datetime.datetime.now().isoformat()
       self.notifications_by_id[notify_id] = {'notify_id':  int(notify_id),
                                              'notify_type':notify_type,
                                              'created':    created,
                                              'updated':    created,
                                              'read':       False,
                                              'seen':       False,
                                              'username':   username,
                                              'data':       data}
   def mark_notification_read(self,notify_id=None):
       self.notifications_by_id[notify_id]['read'] = True
       self.notifications_by_id[notify_id]['updated'] = datetime.datetime.now().isoformat()
   def mark_notification_seen(self,notify_id=None):
       self.notifications_by_id[notify_id]['seen'] = True
       self.notifications_by_id[notify_id]['updated'] = datetime.datetime.now().isoformat()
   def get_notification(self,notify_id=None):
       """ Return a single notification
           If not found, returns None
       """
       if not notify_id in self.notifications_by_id.keys(): return None
       return self.notifications_by_id[notify_id]
   def get_notifications(self,username=None,created_before=None,updated_after=None,read=None,notify_type=None,limit=30):
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
           if not (notify_type is None):
              if v['notify_type'] != notify_type: continue
           retval.append(v)
       return retval[:limit]
