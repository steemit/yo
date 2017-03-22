# coding=utf-8
import logging
import os
import json

log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'))
logging.basicConfig(level=log_level)
logger = logging.getLogger('__name__')


MINUTE = 60
HOUR = MINUTE * 60
DAY = 24 * HOUR
WEEK = 7 * DAY
MONTH = 30 * DAY

HARD_RATE_LIMITS = {
    'email': {
        'hour': 1
    },
    'sms': {
        'hour': 1
    },
    'browser': {
        'minute': 1
    }
}


async def is_ok(notification):
    return True