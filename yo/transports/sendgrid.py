# coding=utf-8
""" Sendgrid transport class
"""
import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *

from yo.email_templates import EmailRenderer
from .base_transport import BaseTransport

logger = logging.getLogger(__name__)


class SendGridTransport(BaseTransport):

    def __init__(self, sendgrid_privkey, templates_dir):
        """ Transport implementation for sendgrid

        Args:
            sendgrid_privkey(str): the private key for sendgrid
            templates_dir(str): the directory containing email templates
        """
        self.privkey = sendgrid_privkey
        self.sg = SendGridAPIClient(apikey=sendgrid_privkey)
        self.renderer = EmailRenderer(templates_dir)

    def send_notification(self, to_subdata=None, to_username=None, notify_type=None, data=None):
        """ Sends a notification to a specific user

        Keyword args:
           to_subdata:       the subscription data for this transport
           to_username(str): the user we're sending to
           notify_type(str): the type of notification we're sending
           data(dict):       a dictionary containing the raw data for the notification

        Note:
           the subscription data for sendgrid is simply an email address
        """
        logger.debug('SendGrid sending notification to %s' % to_subdata)
        from_email = Email('no-reply@steemit.com', 'steemit.com')
        to_email = Email(to_subdata)

        mail_content = None
        try:
            mail_content = self.renderer.render(notify_type, data)
        except Exception as e:
            logger.exception('Exception occurred when rendering email template')
            return

        mail = Mail(from_email)
        mail.subject = mail_content['subject']
        mail.add_content(Content('text/plain', mail_content['text']))
        if mail_content['html'] != None:
            mail.add_content(Content('text/html', mail_content['html']))

        response = self.sg.client.mail.send.post(request_body=mail.get())
        logger.debug('SendGrid response code %s' % response.status_code)
        logger.debug('SendGrid response body %s' % response.body)
        logger.debug('SendGrid response headers %s' % str(response.headers))
