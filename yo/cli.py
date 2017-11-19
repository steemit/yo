# coding=utf-8
import argparse
import os
import sys

from .app import YoApp
from .config import YoConfigManager
from .db import YoDatabase
from .services.api_server import YoAPIServer
from .services.blockchain_follower import YoBlockchainFollower
from .services.notification_sender import YoNotificationSender


def main():
    parser = argparse.ArgumentParser(
        description="Notification service for the steem blockchain")
    parser.add_argument(
        '-c',
        '--config',
        type=str,
        default='./yo.cfg',
        help='Path to the configuration file')
    args = parser.parse_args(sys.argv[1:])

    yo_config = YoConfigManager(args.config)
    yo_database = YoDatabase(db_url=os.environ.get('YO_DATABASE_URL'))
    yo_app = YoApp(config=yo_config, db=yo_database)

    yo_app.add_service(YoNotificationSender)
    yo_app.add_service(YoAPIServer)
    yo_app.add_service(YoBlockchainFollower)
    yo_app.run()


if __name__ == '__main__':
    main()
