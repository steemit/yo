# -*- coding: utf-8 -*-
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import structlog

logger = structlog.getLogger(__name__)

UserType = Dict[str, Any]
NotificationType = Dict[str, Any]
NotificationsList = List[NotificationType]
FailedNotification = Tuple[UserType, NotificationType]
FailedNotificationList = List[FailedNotification]


class AbstractTransport(ABC):
    @abstractmethod
    def process_notifications(
            self, user: UserType,
            notifications: NotificationsList) -> FailedNotificationList:
        pass

    @abstractmethod
    def filter_notification_types(
            self, user: UserType,
            notifications: NotificationsList) -> NotificationsList:
        pass

    @abstractmethod
    def filter_ratelimited(
            self, user: UserType,
            notifications: NotificationsList) -> NotificationsList:
        pass

    @abstractmethod
    def send_notifications(
            self, user: UserType,
            notifications: NotificationsList) -> FailedNotificationList:
        pass

    @abstractmethod
    def check_ratelimit(self, user: UserType,
                        notifications: NotificationsList) -> NotificationsList:
        pass

    @abstractmethod
    def send_notification(self, user: UserType,
                          notitification: NotificationType) -> bool:
        pass

    @abstractmethod
    def get_template(self, notification_type):
        pass

    @abstractmethod
    def render(self, user, notification):
        pass


class BaseTransport(AbstractTransport):
    transport_type = 'base'

    # pylint: disable=unused-argument
    def __init__(self, *args, yo_db=None, **kwargs):
        self.db = yo_db

    # pylint: enable=unused-argument

    def process_notifications(self, user, notifications):
        supported_notifications = self.filter_notification_types(
            user, notifications)
        rate_limited_notifications = self.filter_ratelimited(
            user, supported_notifications)
        failed = self.send_notifications(user, rate_limited_notifications)
        logger.debug(
            'process_notification_results',
            username=user['username'],
            original_count=len(notifications),
            supported_count=len(supported_notifications),
            rate_limited_count=len(rate_limited_notifications),
            failed_count=len(failed))
        return failed

    def filter_notification_types(self, user, notifications):
        supported_types = user['transports'].get(self.transport_type, [])
        filtered = [
            item for item in notifications
            if item['notify_type'] in supported_types
        ]
        logger.debug(
            'filtered on notification type',
            supported_types=supported_types,
            unfiltered_count=len(notifications),
            filtered_count=len(filtered))
        return filtered

    def filter_ratelimited(self, user, notifications):
        filtered = [
            item for item in notifications if self.check_ratelimit(user, item)
        ]
        logger.debug(
            'filtered on ratelimit',
            unfiltered_count=len(notifications),
            filtered_count=len(filtered))
        return filtered

    def send_notifications(self, user, notifications):
        failed = []
        for notification in notifications:
            result = self.send_notification(user, notification)
            if not result:
                logger.error(
                    'send_notification failed', notification=notification)
                failed.append((user, notification))
        return failed

    def check_ratelimit(self, user: UserType,
                        notifications: NotificationsList) -> NotificationsList:
        return notifications

    def send_notification(self, user: UserType,
                          notitification: NotificationType) -> bool:
        return False

    def get_template(self, notification_type):
        pass

    def render(self, user, notification):
        pass
