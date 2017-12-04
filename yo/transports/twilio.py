# -*- coding: utf-8 -*-
"""Twilio transport, sends sms"""

import structlog
from twilio.rest import Client

from .base_transport import BaseTransport

logger = structlog.getLogger(
    __name__, transport='TwilioTranport', transport_type='sms')


class TwilioTransport(BaseTransport):
    transport_type = 'sms'

    def __init__(self, account_sid, auth_token, from_number, *args, **kwargs):
        """Transport implementation for twilio

        Args:
            account_sid(str): the account id for twilio
            auth_token(str):  the auth token for twilio
            from_number(str): the twilio number to send from
        """
        super().__init__(*args, **kwargs)
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number

    # pylint: disable=arguments-differ
    def send_notification(self, user, notification):
        to_sms_number = user['transports']['sms']['subdata']
        notify_type = notification['notify_type']
        logger.debug(
            'Twilio sending notification',
            notify_type=notify_type,
            to_sms_number=to_sms_number)

        message = self.render(user, notification)

        response = self.client.messages.create(
            to=to_sms_number, from_=self.from_number, body=message)

        logger.debug('Twilio response received', response=response)

    # pylint: enable=arguments-differ

    def render(self, user, notification):
        raise NotImplementedError
