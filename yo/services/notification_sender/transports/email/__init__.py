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


async def send_email(notification):
    asyncio.sleep(1)




async def handle_email_transport(pool):
    conn = await pool.acquire()
    while True:
        loop_start = time.perf_counter()
        # begin transaction
        transport_type = TransportType['email']
        loop_start = time.perf_counter()
        # begin transaction
        async with QItem(conn, transport_type=transport_type) as item:
            logger.debug('qitem received', item_str=item)
            time_to_acquire_item = time.perf_counter() - loop_start
            rates = await get_rates(conn, item['to_username'],transport_type)
            if rates or True:
                user_email = await get_user_email(item['to_username'])
                result = await send_email(item, user_email)
                time_to_send = time.perf_counter() - time_to_acquire_item
                await sent(conn, item['nid'], item['to_username'], transport_type.value)
                time_to_mark_sent = time.perf_counter() - time_to_send
            else:
                time_to_send = 0
                time_to_mark_sent = 0

        logger.debug('email notification processed',
                     acquire_item=time_to_acquire_item,
                     send_item=time_to_send,
                     mark_sent=time_to_mark_sent,
                     loop_total=time.perf_counter() - loop_start)



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
