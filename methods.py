# coding=utf-8
import logging

from jsonrpcserver.aio import methods

logger = logging.getLogger(__name__)

# event triggered method
@methods.add('yo.event')
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

# user methods
@methods.add('yo.create_user')
async def create_user(user=None, db=None):
    pass

@methods.add('yo.update_user')
async def update_user(user=None, db=None):
    pass

# notification methods
@methods.add('yo.get_notification_status')
async def get_notification_status(notification=None, db=None):
    pass

@methods.add('yo.mark_notification_as_seen')
async def mark_notification_as_seen(notification=None, db=None):
    pass

@methods.add('yo.mark_notification_as_read')
async def mark_notification_as_read(notification=None, db=None):
    pass

# direct transport methods
@methods.add('yo.send_email')
async def send_email(to_email=None, from_email=None, subject=None, content=None, content_type=None, db=None):
    pass

@methods.add('yo.send_sms')
async def send_sms(to=None, _from=None, body=None, db=None):
    pass

@methods.add('yo.send_browser_notification')
async def send_browser_notification(reg_ids=None, data=None, db=None, **kwargs):
    pass
