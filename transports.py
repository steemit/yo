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


@methods.add('yo.send_email')
async def send_email(**kwargs):
    '''
    "sendgrid": {
    "from": "SDC_SENDGRID_FROM",
    "key": "SDC_SENDGRID_API_KEY",
    "templates": {
      "confirm_email": "SDC_SENDGRID_CONFIRMTEMPLATE",
      "waiting_list_invite": "SDC_SENDGRID_WAITINGTEMPLATE"
    }
  },

    Args:
        **kwargs ():

    Returns:

    '''

    # https://github.com/steemit/condenser/blob/master/server/sendEmail.js
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("test@example.com")
    subject = "Hello World from the SendGrid Python Library!"
    to_email = Email("test@example.com")
    content = Content("text/plain", "Hello, Email!")
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())


@methods.add('yo.send_sms')
async def send_sms(**kwargs):
    '''
  "twilio": {
    "account_sid": "SDC_TWILIO_ACCOUNT_SID",
    "auth_token": "SDC_TWILIO_AUTH_TOKEN"
  },

    '''

    account = "ACXXXXXXXXXXXXXXXXX"
    token = "YYYYYYYYYYYYYYYYYY"
    client = TwilioRestClient(account, token)

    message = client.messages.create(to="+12316851234", from_="+15555555555",
                                     body="Hello there!")

@methods.add('yo.send_browser_notification')
async def send_browser_notification(**kwargs):
    # https://github.com/steemit/condenser/blob/master/server/api/notifications.js
    # https://developers.google.com/cloud-messaging/
    gcm = GCM(API_KEY)
    data = {'param1': 'value1', 'param2': 'value2'}

    # Downstream message using JSON request
    reg_ids = ['token1', 'token2', 'token3']
    response = gcm.json_request(registration_ids=reg_ids, data=data)

    # Downstream message using JSON request with extra arguments
    res = gcm.json_request(
            registration_ids=reg_ids, data=data,
            collapse_key='uptoyou', delay_while_idle=True, time_to_live=3600
    )

    # Topic Messaging
    topic = 'topic name'
    gcm.send_topic_message(topic=topic, data=data)


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


'''
"sendgrid": {
    "from": "noreply@example.com",
    "key": "SG.xxx_yyyy",
    "templates": {
      "confirm_email": false,
      "waiting_list_invite": false
    }
  },
  "telesign": {
    "customer_id": false,
    "rest_api_key": false
  },
  "twilio": {
    "account_sid": false,
    "auth_token": false
  }



  "sendgrid": {
    "from": "SDC_SENDGRID_FROM",
    "key": "SDC_SENDGRID_API_KEY",
    "templates": {
      "confirm_email": "SDC_SENDGRID_CONFIRMTEMPLATE",
      "waiting_list_invite": "SDC_SENDGRID_WAITINGTEMPLATE"
    }
  },
  "telesign": {
    "customer_id": "SDC_TELESIGN_CUSTOMER_ID",
    "rest_api_key": "SDC_TELESIGN_API_KEY"
  },


'''

