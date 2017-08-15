# coding=utf-8
import logging
import os
import json


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


async def check_rate_limit(notification, uid):
    return True