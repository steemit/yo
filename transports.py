# coding=utf-8
import logging
import os
import asyncio

from twilio.rest import TwilioRestClient
from gcm import GCM
import sendgrid
from sendgrid.helpers.mail import Email
from sendgrid.helpers.mail import Mail
from sendgrid.helpers.mail import Content
from jsonrpcserver.aio import methods

log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'))
logging.basicConfig(level=log_level)
logger = logging.getLogger('__name__')

sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
SENDGRID_FROM_EMAIL = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@example.com')

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

GCM_API_KEY = os.environ.get('GCM_API_KEY')
google_cloud_messenger = GCM(GCM_API_KEY)

TELESIGN_CUSTOMER_ID = os.environ.get('TELESIGN_CUSTOMER_ID')
TELESIGN_API_KEY = os.environ.get('TELESIGN_API_KEY')


async def send_email(to_email=None, from_email=None, subject=None, content=None, content_type=None):
    '''

    Args:
        to_email (str):
        from_email (str):
        subject (str):
        content (str):
        content_type (str):

    Returns:
        response ():
    '''

    # https://github.com/steemit/condenser/blob/master/server/sendEmail.js
    to_email = Email(to_email)
    from_email = from_email or SENDGRID_FROM_EMAIL
    from_email = Email(from_email)
    content_type = content_type or 'text/plain'
    content = Content(content_type, content)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    return response


async def send_sms(to=None, _from=None, body=None):
    '''

    Args:
        to (str):
        _from (str):
        body (str):

    Returns:
        message ():
    '''
    message = client.messages.create(to=to, _from=_from, body=body)
    return message


async def send_browser_notification(reg_ids=None, data=None, **kwargs):
    '''

    Args:
        reg_ids (List(str)):
        data (str):
        **kwargs ():

    Returns:
        response ():

    '''

    # https://github.com/steemit/condenser/blob/master/server/api/notifications.js
    # https://developers.google.com/cloud-messaging/

    # Downstream message using JSON request
    response = google_cloud_messenger.json_request(registration_ids=reg_ids, data=data, **kwargs)
    return response


async def send(notification):
    transport = notification['transport']
    if transport == 'browser':
        pass
    elif transport == 'sms':
        pass
    elif transport == 'email':
        pass
    elif transport == 'web':
        pass
    else:
        raise ValueError('Bad transport %s', transport)
