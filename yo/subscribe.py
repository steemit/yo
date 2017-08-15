# -*- coding: utf-8 -*-
import logging
import os

from functools import partial
from collections import defaultdict

from funcy.py3 import log_calls, log_errors

import notification

log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'))
logging.basicConfig(level=log_level)
logger = logging.getLogger('__name__')


_subscriptions = defaultdict(list)


def _subscribe(subscriptions, function, event):
    """Subscribe a function to the list::
        subscriptions.subscribe(function, event)

    Alternatively, use as a decorator::

        @subscribe(event)
        def function(arg1, kwarg1=True):
            if kwarg1:
                return arg1

    """

    @log_calls(logger.debug, errors=False)
    @log_errors(logger.exception)
    def wrapped(function):
        return function

    subscriptions[event].append(wrapped)
    return function

def _unsubscribe(subscriptions, function, event):
    try:
        subscriptions[event].remove(function)
    except ValueError as e:
        logger.warning('attempted to unsubcribed a non-existant subscription')


def _dispatch(subscriptions, pool, event, *args, **kwargs):
    for func in subscriptions[event]:
        try:
            notifications = func(event, *args, **kwargs)
        except Exception as e:
            logger.exception('failed to process notification', extra=notification)
        else:
            for item in notifications:
                notification.notify(pool, item)
    else:
        logger.warning('dispatched empty subscriptions for %s', event)


subscribe = partial(_subscribe, _subscriptions)
unsubscribe = partial(_unsubscribe, _subscriptions)
dispatch = partial(_dispatch, _subscriptions)