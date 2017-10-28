# coding=utf-8
"""Twilio transport, sends sms"""

from twilio.rest import Client

from .base_transport import BaseTransport
import logging

logger = logging.getLogger(__name__)


class TwilioTransport(BaseTransport):

    def __init__(self, account_sid, auth_token, from_number):
        """Transport implementation for twilio

        Args:
            account_sid(str): the account id for twilio
            auth_token(str):  the auth token for twilio
            from_number(str): the twilio number to send from
        """
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number

    def send_notification(self, to_subdata=None, notify_type=None, data=None):
        if data is None:
            data = {}
        logger.debug('Twilio sending notification %s to %s',
                     notify_type, to_subdata)

        if notify_type == 'vote':
            vote_info = data['op'][1]
            message = 'Your comment or post %s has been upvoted by %s' % (
                vote_info['permlink'], vote_info['voter'])
        else:
            logger.error('Twilio - unknown notification type: %s', notify_type)
            return

        response = self.client.messages.create(
            to=to_subdata,
            from_=self.from_number,
            body=message)
        logger.debug('Twilio response %s', response)
