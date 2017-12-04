# -*- coding: utf-8 -*-

import structlog
from toolz.itertoolz import groupby

from ..transports import sendgrid
from ..transports import twilio
from .base_service import YoBaseService

logger = structlog.getLogger(__name__, service_name='notification_sender')


class YoNotificationSender(YoBaseService):
    service_name = 'notification_sender'

    def __init__(self, yo_app=None, config=None, db=None):
        super().__init__(yo_app=yo_app, config=config, db=db)
        self.configured_transports = {}

    async def api_trigger_notifications(self):
        await self.main_task()
        return {'result': 'Succeeded'}  # FIXME

    async def main_task(self):
        unsents = self.db.get_db_unsents()
        self.log.info('main task', unsent_count=len(unsents))

        grouped_unsents = groupby('to_username', unsents)

        failed_sends = []
        for username, unsents in grouped_unsents.items():
            for transport in self.configured_transports.values():
                failed = transport.process_notifications(username, unsents)
                failed_sends.extend(failed)

        failed_sends_ids = set(item[1]['nid'] for item in failed_sends)
        sent_notifications = [
            item for item in unsents if item['nid'] not in failed_sends_ids
        ]
        sent_nids = [n['nid'] for n in sent_notifications]
        self.db.mark_db_notifications_sent(sent_nids)

    # pylint: disable=abstract-class-instantiated
    def init_api(self):
        super().init_api()
        config = self.yo_app.config.config_data

        self.private_api_methods['trigger_notifications'] = \
            self.api_trigger_notifications

        if config['sendgrid'].getint('enabled', 0):
            self.log.info('Enabling sendgrid (email) transport')
            self.configured_transports['email'] = \
                sendgrid.SendGridTransport(config['sendgrid']['priv_key'],
                                           config['sendgrid']['templates_dir'],
                                           yo_db=self.db)

        if config['twilio'].getint('enabled', 0):
            self.log.info('Enabling twilio (sms) transport')
            self.configured_transports['sms'] = \
                twilio.TwilioTransport(config['twilio']['account_sid'],
                                       config['twilio']['auth_token'],
                                       config['twilio']['from_number'],
                                       yo_db=self.db)
