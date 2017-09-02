import logging
logger = logging.getLogger(__name__)

from .db import *

def check_ratelimit(notification_object,override=False):
    """Checks if this notification should be sent or not

    Args:
        notification_object(dict): The notification in question, must contain the priority field (priority_level)
    Keyword args:
        override(bool): If set True, will use the hard limits instead of soft

    Returns:
        True if allowed, False if not
    """
    notification_priority = notification_object['priority_level']
    to_username           = notification_object['to_username']

    if notification_priority==PRIORITY_ALWAYS:
       
    elif notification_priority==PRIORITY_PRIORITY:
    elif notification_priority==PRIORITY_NORMAL:
    elif notification_priority==PRIORITY_LOW:
    elif notification_priority==PRIORITY_MARKETING:
    else:
      logger.error('Invalid notification priority level! Assuming corrupted data for notification: %s' % notification_object)

    return True # dummy for now
