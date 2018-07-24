# -*- coding: utf-8 -*-
"""Twilio transport, sends sms"""

import structlog
import toolz
from twilio.rest import Client

from .base_transport import BaseTransport

logger = structlog.getLogger(__name__, transport='TwilioTranport', transport_type='sms')




async def handle_sms(conn, item):
    transport_type = TransportType['sms']
    rates = await get_rates(conn, item['to_username'], transport_type)
    if rates or True:
        user_phone = await get_user_phone(item['to_username'])
        result = await send_sms(item, user_phone)
        await sent(conn, item['nid'], item['to_username'], transport_type.value)
        time_to_mark_sent = time.perf_counter() - time_to_send
    else:
        time_to_send = 0
        time_to_mark_sent = 0



# pylint: disable=pointless-string-statement
class TwilioTransport(BaseTransport):
    transport_type = 'sms'

    def __init__(self, account_sid=None, auth_token=None, from_number=None):
        """Transport implementation for twilio

        Args:
            account_sid(str): the account id for twilio
            auth_token(str):  the auth token for twilio
            from_number(str): the twilio number to send from
        """
        self.can_send = False
        if account_sid and auth_token and from_number:
            self.can_send = True
            self.client = Client(account_sid, auth_token)
            self.from_number = from_number
        # pylint: disable=global-statement
        global logger
        logger = logger.bind(can_send=self.can_send)
        logger.info('configured')

    # pylint: disable=arguments-differ
    def send_notification(self, notification):
        to_sms_number = toolz.get_in(notification, ['transports', 'sms', 'subdata'])
        notify_type = notification['notify_type']
        logger.debug(
            'send_notifiction', notify_type=notify_type, to_sms_number=to_sms_number)
        if self.can_send:
            message = self.render(notification)
            logger.debug('send_notification', message=message)

            response = self.client.messages.create(
                to=to_sms_number, from_=self.from_number, body=message)
            logger.debug('Twilio response received', response=response)
        return notification

    # pylint: enable=arguments-differ

    def render(self, notification):
        raise NotImplementedError()
