# coding=utf-8
import logging

from yo import transports

from yo import storage
from yo.storage import users

from jsonrpcserver.aio import methods
import json

logger = logging.getLogger(__name__)

def add_api_method(func):
    """ Used to add the yo. prefix
    """
    methods.add(func,name='yo.%s' % func.__name__)

# test method
@add_api_method
async def test(db=None):
      return {'alive':True}

# event triggered method
@add_api_method
async def event(event=None, db=None):
    '''

    :param event:
    :type event:
    :return:
    :rtype:
    
    filter event
    if not event:
        return
    get notification types for event
    if not notification types:
        return
    create notification
    store notification
        if not notification stored:
            error
    if rate_limit_not_exceeded(notification):
        send notification
            if not noticifcation sent:
                error

    
    '''
    pass

# TODO - needs some auth framework here

# user methods
@add_api_method
async def create_user(user=None, db=None):
      retval = None
      try:
         result = await storage.users.put(db,user)
      except Exception as e:
         logger.exception('Failed to create user',extra=retval)
      return retval

@add_api_method
async def create_email_subscription(to_uid=None, email=None, db=None):
      sub_object = {'to_uid':to_uid,'email':email}
      retval = None
      try:
         result = await storage.emailsubs.put(db,sub_object)
      except Exception as e:
         logger.exception('Failed to create email subscription',extra=retval)
      return retval

@add_api_method
async def update_user(user=None, db=None):
    pass

# notification methods
@add_api_method
async def get_notification_status(notification=None, db=None):
    pass

@add_api_method
async def mark_notification_as_seen(notification=None, db=None):
    pass

@add_api_method
async def mark_notification_as_read(notification=None, db=None):
    pass

# direct transport methods
# TODO - should this really exist here?
@add_api_method
async def send_email(to_email=None, from_email=None, subject=None, content=None, content_type=None, db=None):
    pass

@add_api_method
async def send_sms(to=None, _from=None, body=None, db=None):
    pass

@add_api_method
async def send_email_notification(to_uid=None, notify_type=None, data=None, db=None):
     notification_object = {'transport'   :'email',
                            'type'        :notify_type,
                            'source_event':json.dumps({}),
                            'data'        :data}
     await transports.send(notification_object)

@add_api_method
async def send_email_message(to_uid=None, from_username=None, msg=None, db=None):
     user_profile = await users.get(db,to_uid)
     notification_data = {'to'             :to_uid,
                          'fromusername'   :from_username,
                          'touserfirstname':user_profile['first_name'],
                          'touserlastname' :user_profile['last_name'],
                          'message'        :msg}
     await transports.send({'to':to_uid,
                          'transport'   :'email',
                          'type'        :'message',
                          'source_event':json.dumps({}),
                          'data'        :notification_data})

@add_api_method
async def send_browser_notification(to_uid=None, notify_type=None, data=None, db=None):
     notification_object = {'transport'   :'browser',
                            'type'        :notify_type,
                            'source_event':json.dumps({}),
                            'data'        :data}
     await transports.send(notification_object)
     
