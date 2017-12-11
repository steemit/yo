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
NotificationResults = Tuple[List, List, List, List]


class AbstractTransport(ABC):
    @abstractmethod
    def process_notifications(self, user_rates,
                              notifications: NotificationsList) -> NotificationResults:
        pass

    @abstractmethod
    def filter_notification_types(self,
                                  notifications: NotificationsList) -> NotificationsList:
        pass

    @abstractmethod
    def filter_ratelimited(self, user_rates,
                           notifications: NotificationsList) -> NotificationsList:
        pass

    @abstractmethod
    def send_notifications(self, notifications: NotificationsList) -> NotificationResults:
        pass

    @abstractmethod
    def check_ratelimit(self, user_rates, notifications: NotificationsList) -> bool:
        pass

    @abstractmethod
    def send_notification(self, notitification: NotificationType) -> bool:
        pass

    @abstractmethod
    def get_template(self, notification_type):
        pass

    @abstractmethod
    def render(self, notification):
        pass


class BaseTransport(AbstractTransport):
    transport_type = 'base'

    def process_notifications(self, user_rates, notifications):
        notifications, muted = self.filter_notification_types(notifications)

        notifications, rate_limited = self.filter_ratelimited(user_rates, notifications)

        sent, failed = self.send_notifications(notifications)

        logger.debug(
            'process_notification_results',
            original_count=len(notifications),
            muted_count=len(muted),
            rate_limited_count=len(rate_limited),
            sent_count=len(sent),
            failed_count=len(failed))

        return self.transport_type, sent, failed, muted, rate_limited

    def filter_notification_types(self, notifications):
        supported, muted = [], []
        for notification in notifications:
            supported_types = set(notification['transports'].get(self.transport_type, []))
            if notification['notify_type'] in supported_types:
                supported.append(notification)
            else:
                muted.append(notification)
        logger.debug(
            'filtered on notification type',
            supported_count=len(supported),
            muted_count=len(muted))
        return supported, muted

    def filter_ratelimited(self, user_rates, notifications):
        allowed, rate_limited = [], []
        for notification in notifications:
            if self.check_ratelimit(user_rates, notification):
                allowed.append(notification)
            else:
                rate_limited.append(notification)

        logger.debug(
            'filtered on ratelimit',
            unfiltered_count=len(allowed),
            filtered_count=len(rate_limited))
        return allowed, rate_limited

    def send_notifications(self, notifications):
        sent, failed = [], []
        for notification in notifications:
            result = self.send_notification(notification)
            if not result:
                logger.error(
                    'send_notification failed', notification=notification, result=result)
                failed.append(notification)
            else:
                sent.append(notification)
        return sent, failed

    def check_ratelimit(self, user_rates, notifications: NotificationsList) -> bool:
        return True

    def send_notification(self, notitification: NotificationType) -> bool:
        return False

    def get_template(self, notification_type):
        pass

    def render(self, notification):
        pass
