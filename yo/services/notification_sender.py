# -*- coding: utf-8 -*-

import structlog

from ..transports import sendgrid
from ..transports import twilio
from .base_service import YoBaseService

logger = structlog.getLogger(__name__, service_name='notification_sender')


class YoNotificationSender(YoBaseService):
    service_name = 'notification_sender'

    def __init__(self, yo_app=None, config=None, db=None):
        super().__init__(yo_app=yo_app, config=config, db=db)
        self._configured_transports = {}

    async def main_task(self):
        unsents = self.db.get_db_unsents()
        usernames = set(u['to_username'] for u in unsents)
        self.log.info(
            'sending unsents', unsent_count=len(unsents), unique_usernames=len(usernames))

        user_rates = self.db.get_users_rates(usernames)
        logger.debug('main_task', user_rates=user_rates)
        results = [
            transport.process_notifications(user_rates, unsents)
            for transport in self.configured_transports
        ]

        logger.debug('results', results=results)
        #results = [transport.process_notifications(user_rates, unsents) for transport in self.configured_transports]
        for transport_type, sent, failed, muted, rate_limited in results:
            self.log.debug('storing results', transport=transport_type)
            self.db.store_notification_results(transport_type, sent, failed, muted,
                                               rate_limited)

    @property
    def configured_transports(self):
        return self._configured_transports.values()

    # pylint: disable=abstract-class-instantiated
    def init_api(self):
        super().init_api()
        config = self.yo_app.config

        # pylint: disable=using-constant-test

        self.log.info('enabling sendgrid (email) transport')
        self._configured_transports['email'] = \
            sendgrid.SendGridTransport(config.sendgrid_priv_key,
                                       config.sendgrid_templates_dir)

        self.log.info('Enabling twilio (sms) transport')
        self._configured_transports['sms'] = \
            twilio.TwilioTransport(config.twilio_account_sid,
                                   config.twilio_auth_token,
                                   config.twilio_from_number)
