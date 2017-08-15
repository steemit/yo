# -*- coding: utf-8 -*-
# coding=utf-8
import logging
import os


import transports
import storage

log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'))
logging.basicConfig(level=log_level)
logger = logging.getLogger('__name__')


def notify(pool, notification, *args, **kwargs):
    try:
        result = storage.put(notification)
        notificiation = storage.get(result.id)
    except Exception as e:
        logger.exception('failed to store notification', extra=notification)
        return

    try:
        result = transports.send(notification)
        if not result:
            raise Exception('failed to send notification', extra=notification)
    except Exception as e:
        logger.error(e, extra=notification)
        return

    try:
        storage.mark_as_sent(notification)
    except Exception as e:
        logger.error('failed to mark notification as sent', extra=notification)