# -*- coding: utf-8 -*-
""" Sendgrid transport class
"""
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Content
from sendgrid.helpers.mail import Email
from sendgrid.helpers.mail import Mail
import structlog

from ..email_templates import EmailRenderer
from .base_transport import BaseTransport

logger = structlog.getLogger(
    __name__, transport='SendGridTranport', transport_type='email')


class SendGridTransport(BaseTransport):
    transport_type = 'email'

    def __init__(self, sendgrid_privkey, templates_dir, *args, **kwargs):
        """ Transport implementation for sendgrid

        Args:
            sendgrid_privkey(str): the private key for sendgrid
            templates_dir(str): the directory containing email templates
        """
        super().__init__(*args, **kwargs)
        self.privkey = sendgrid_privkey
        self.sg = SendGridAPIClient(apikey=sendgrid_privkey)
        self.renderer = EmailRenderer(templates_dir)

    # pylint: disable=arguments-differ
    def send_notification(self, user, notification):
        to_email = user['transports']['email']['subdata']
        logger.debug('SendGrid sending notification', to_email=to_email)
        from_email = Email('no-reply@steemit.com', 'steemit.com')

        mail_content = self.render(user, notification)

        mail = Mail(
            from_email=from_email,
            to_email=to_email,
            subject=mail_content['subject'],
            content=Content('text/plain', mail_content['text']))

        if mail_content['html'] is not None:
            mail.add_content(Content('text/html', mail_content['html']))

        response = self.sg.client.mail.send.post(request_body=mail.get())

        logger.debug(
            'SendGrid response',
            code=response.status_code,
            body=response.body,
            headers=response.headers)
        return True

    # pylint: enable=arguments-differ

    def render(self, user, notification):
        try:
            return self.renderer.render(notification['notify_type'],
                                        notification)
        except Exception:
            logger.exception(
                'Exception occurred when rendering email template')
            return False
