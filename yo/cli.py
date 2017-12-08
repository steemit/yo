# -*- coding: utf-8 -*-
import argparse
import os

from .app import YoApp
from .db import YoDatabase
from .services.blockchain_follower import YoBlockchainFollower
from .services.notification_sender import YoNotificationSender


def main():
    parser = argparse.ArgumentParser(description="Steem notification service")
    parser.add_argument('--log_level', default=os.environ.get('LOG_LEVEL', 'INFO'))
    parser.add_argument(
        '--steemd_url', default=os.environ.get('STEEMD_URL', 'https://api.steemit.com'))
    parser.add_argument(
        '--database_url', default=os.environ.get('DATABASE_URL', 'sqlite://'))
    parser.add_argument(
        '--sendgrid_priv_key', default=os.environ.get('SENDGRID_PRIV_KEY', None))
    parser.add_argument(
        '--sendgrid_templates_dir',
        default=os.environ.get('SENDGRID_TEMPLATES_DIR', 'mail_templates'))
    parser.add_argument(
        '--twilio_account_sid', default=os.environ.get('TWILIO_ACCOUNT_SID', None))
    parser.add_argument(
        '--twilio_auth_token', default=os.environ.get('TWILIO_AUTH_TOKEN', None))
    parser.add_argument(
        '--twilio_from_number', default=os.environ.get('TWILIO_FROM_NUMBER', None))
    parser.add_argument(
        '--steemd_start_block', default=os.environ.get('STEEMD_START_BLOCK', None))
    parser.add_argument('--http_host', default=os.environ.get('HTTP_HOST', '0.0.0.0'))
    parser.add_argument(
        '--http_port', type=int, default=os.environ.get('HTTP_PORT', 8080))
    args = parser.parse_args()

    yo_database = YoDatabase(db_url=args.database_url)
    yo_app = YoApp(config=args, db=yo_database)
    yo_app.add_service(YoNotificationSender)
    yo_app.add_service(YoBlockchainFollower)
    yo_app.run()


if __name__ == '__main__':
    main()
