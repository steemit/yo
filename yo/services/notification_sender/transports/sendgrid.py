# -*- coding: utf-8 -*-
""" Sendgrid transport class
"""
import structlog
import toolz
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Content
from sendgrid.helpers.mail import Email
from sendgrid.helpers.mail import Mail

from services.notification_sender.email_templates import EmailRenderer
from .base_transport import BaseTransport

logger = structlog.getLogger(
    __name__, transport='SendGridTranport', transport_type='email')


# pylint: disable=pointless-string-statement
class SendGridTransport(BaseTransport):
    transport_type = 'email'

    def __init__(self, sendgrid_privkey=None, sendgrid_templates_dir=None):
        """ Transport implementation for sendgrid

        Args:
            sendgrid_privkey(str): the private key for sendgrid
            templates_dir(str): the directory containing email templates
        """

        self.can_send = False
        if sendgrid_privkey and sendgrid_templates_dir:
            self.can_send = True
            self.privkey = sendgrid_privkey
            self.templates_dir = sendgrid_templates_dir
            self.sg = SendGridAPIClient(apikey=self.privkey)
            self.renderer = EmailRenderer(self.templates_dir)
        # pylint: disable=global-statement
        global logger
        logger = logger.bind(can_send=self.can_send)
        logger.info('configured')

    # pylint: disable=arguments-differ
    def send_notification(self, notification):
        if self.can_send:
            to_email = toolz.get_in(notification, ['transports', 'sms', 'subdata'])
            logger.debug('SendGrid sending notification', to_email=to_email)
            from_email = Email('no-reply@steemit.com', 'steemit.com')

            mail_content = self.render(notification)

            mail = Mail(
                from_email=from_email,
                to_email=to_email,
                subject=mail_content['subject'],
                content=Content('text/plain', mail_content['text']))

            if mail_content['html'] is not None:
                mail.add_content(Content('text/html', mail_content['html']))

            logger.debug('send_notification', mail=mail)

            response = self.sg.client.mail.send.post(request_body=mail.get())

            logger.debug(
                'SendGrid response',
                code=response.status_code,
                body=response.body,
                headers=response.headers)
        return notification

    # pylint: enable=arguments-differ
    def render(self, notification):
        try:
            return self.renderer.render(notification['notify_type'], notification)
        except Exception:
            logger.exception('Exception occurred when rendering email template')
            return False
