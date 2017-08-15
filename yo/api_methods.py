# coding=utf-8
import logging
import storage
import storage.users

from jsonrpcserver.aio import methods

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
@add_api_method
async def send_email(to_email=None, from_email=None, subject=None, content=None, content_type=None, db=None):
    pass

@add_api_method
async def send_sms(to=None, _from=None, body=None, db=None):
    pass

@add_api_method
async def send_browser_notification(reg_ids=None, data=None, db=None, **kwargs):
    pass
