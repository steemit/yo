import yo
import os
import sys
import argparse

from yo.app import YoApp
from yo.config import YoConfigManager
from yo.db import YoDatabase
from yo.blockchain_follower import YoBlockchainFollower
from yo.notification_sender import YoNotificationSender
from yo.api_server import YoAPIServer


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


    sender = YoNotificationSender(config=yo_config, db=yo_database)
    yo_app.add_service(sender)

    api_server = YoAPIServer()
    yo_app.add_service(api_server)


    follower = YoBlockchainFollower(config=yo_config, db=yo_database)
    yo_app.add_service(follower)
    yo_app.run()


if __name__ == '__main__':
    main()
