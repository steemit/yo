""" Maintains in-memory mock notifications
"""

class YoMockData:
   """ A set of in-memory mock notifications
   """
   def __init__(self):
       self.reset()
   def reset(self):
       """ Reset the current status of the mock notifications
           Also freshly generates a new set of data
       """
       self.add_new_notification(notify_type='power_down',username='test_user',data=dict(amount=6.66))
       self.add_new_notification(notify_type='power_up',username='test_user',data=dict(amount=13.37))
       self.add_new_notification(notify_type='resteem',username='test_user',data=dict(resteemed_item=dict(author='test_user',category='test',permlink='test-post',summary='A test post',resteemed_by='some_user')))

   def add_new_notification(self,notify_type=None,created=None,username=None,data={}):
       pass
   def mark_notification_read(self,notify_id=None):
       pass
   def mark_notification_seen(self,notify_id=None):
       pass
   def get_notifications(self,username=None,created_before=None,updated_after=None,read=None,notify_type=None):
       pass
