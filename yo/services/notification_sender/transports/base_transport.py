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
    async def process_notifications(self,
                              notifications: NotificationsList) -> NotificationResults:
        pass

    @abstractmethod
    async def send_notification(self, notitification: NotificationType) -> bool:
        pass


    @abstractmethod
    def get_template(self, notification_type):
        pass

    @abstractmethod
    def render(self, notification):
        pass


class BaseTransport(AbstractTransport):
    transport_type = 'base'

    def process_notifications(self, notifications):

        sent, failed = self.send_notifications(notifications)

        logger.debug(
            'process_notification_results',
            original_count=len(notifications),

            sent_count=len(sent),
            failed_count=len(failed))

        return self.transport_type, sent, failed

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


    def send_notification(self, notitification: NotificationType) -> bool:
        return False

    def get_template(self, notification_type):
        pass

    def render(self, notification):
        pass
