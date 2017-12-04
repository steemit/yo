# -*- coding: utf-8 -*-
""" wwwpoll transport class

    This handles the notifications accessible via the API with polling (as used by condenser).
    "delivery" basically means storing the notification into the wwwpoll table where it can be polled using the API.
"""

import structlog

from .base_transport import BaseTransport

logger = structlog.getLogger(
    __name__, transport='WWWPollTransport', transport_type='wwwpoll')


class WWWPollTransport(BaseTransport):
    transport_type = 'wwwpoll'

    # pylint: disable=unused-argument,arguments-differ
    def send_notification(self, user, notification):
        return True
