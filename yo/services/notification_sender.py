# -*- coding: utf-8 -*-
import datetime
import json
import logging

from ..db import notifications_table
from ..ratelimits import check_ratelimit
from ..transports import sendgrid
from ..transports import twilio
from ..transports import wwwpoll
from .base_service import YoBaseService

logger = logging.getLogger(__name__)
""" Basic design:

     1. Blockchain sender inserts notification into DB
     2. Blockchain sender triggers the notification by calling internal API method
     3. Notification sender checks if the notification is already sent or not, if not it sends to all configured transports and updates it to sent
"""


class YoNotificationSender(YoBaseService):
    service_name = 'notification_sender'

    def __init__(self, yo_app=None, config=None, db=None):
        super().__init__(yo_app=yo_app, config=config, db=db)
        self.configured_transports = {}

    async def api_trigger_notification(self, username=None):
        logger.info('api_trigger_notification invoked for %s', username)
        await self.run_send_notify({'to_username': username})
        return {'result': 'Succeeded'}  # FIXME

    async def run_send_notify(self, notification_job):
        logger.debug('run_send_notify executing! %s', notification_job)
        user_transports = self.db.get_user_transports(
            notification_job['to_username'])
        user_notify_types_transports = {
        }  # map notification types to the transports enabled for them
        for transport_name, transport_data in user_transports.items():
            for notify_type in transport_data['notification_types']:
                if notify_type not in user_notify_types_transports:
                    user_notify_types_transports[notify_type] = []
                user_notify_types_transports[notify_type].append(
                    (transport_name, transport_data['sub_data']))
        with self.db.acquire_conn() as conn:
            query = notifications_table.select().where(
                notifications_table.c.to_username == notification_job[
                    'to_username'])
            # TODO - add check for already sent
            select_response = conn.execute(query)
            for row in select_response:
                row_dict = dict(row.items())
                if not check_ratelimit(self.db, row_dict):
                    logger.debug(
                        'Skipping sending of notification for failing rate limit check: %s',
                        str(row))
                    continue
                logger.debug('>>>>>> Sending new notification: %s', str(row))

                for t in user_notify_types_transports[row_dict['type']]:
                    logger.debug('Sending notification to transport %s',
                                 str(t[0]))
                    try:
                        t[0].send_notification(
                            to_subdata=t[1],
                            to_username=notification_job['to_username'],
                            notify_type=row['type'],
                            data=json.loads(row['json_data']))
                    except Exception:
                        logger.exception('Transport failed')
                # TODO - check actually sent here, and check per transport - if failing
                # only on a single transport, retry only single transport
                row_dict['sent'] = True
                row_dict['sent_at'] = datetime.datetime.now()
                # pylint: disable=no-value-for-parameter
                update_query = notifications_table.update().where(
                    notifications_table.c.nid == row.nid).values(sent=True)
                # pylint: enable=no-value-for-parameter
                conn.execute(update_query)

    def init_api(self):
        self.private_api_methods[
            'trigger_notification'] = self.api_trigger_notification
        if self.yo_app.config.config_data['wwwpoll'].getint('enabled', 1):
            logger.info('Enabling wwwpoll transport')
            self.configured_transports['wwwpoll'] = wwwpoll.WWWPollTransport(
                self.db)
        if self.yo_app.config.config_data['sendgrid'].getint('enabled', 0):
            logger.info('Enabling sendgrid (email) transport')
            self.configured_transports['email'] = sendgrid.SendGridTransport(
                self.yo_app.config.config_data['sendgrid']['priv_key'],
                self.yo_app.config.config_data['sendgrid']['templates_dir'])
        if self.yo_app.config.config_data['twilio'].getint('enabled', 0):
            logger.info('Enabling twilio (sms) transport')
            self.configured_transports['sms'] = twilio.TwilioTransport(
                self.yo_app.config.config_data['twilio']['account_sid'],
                self.yo_app.config.config_data['twilio']['auth_token'],
                self.yo_app.config.config_data['twilio']['from_number'],
            )

    async def async_task(self):
        pass
