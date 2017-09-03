import logging
logger = logging.getLogger(__name__)

from .db import *

def check_ratelimit(db,notification_object,override=False):
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
       return (db.get_priority_count(to_username,PRIORITY_ALWAYS,3600) < 10)
    elif notification_priority==PRIORITY_PRIORITY:
       if override:
          return (db.get_priority_count(to_username,PRIORITY_PRIORITY,3600) <= 10)
       else:
          return (db.get_priority_count(to_username,PRIORITY_PRIORITY,3600) == 0)
    elif notification_priority==PRIORITY_NORMAL:
       if override:
          return (db.get_priority_count(to_username,PRIORITY_NORMAL,60) < 3)
       else:
          return (db.get_priority_count(to_username,PRIORITY_NORMAL,60) == 0)
    elif notification_priority==PRIORITY_LOW:
       if override:
          return (db.get_priority_count(to_username,PRIORITY_LOW,3600) < 10)
       else:
          return (db.get_priority_count(to_username,PRIORITY_LOW,3600) == 0)
    elif notification_priority==PRIORITY_MARKETING:
       if override:
          return (db.get_priority_count(to_username,PRIORITY_MARKETING,86400) == 0)
       else:
          return (db.get_priority_count(to_username,PRIORITY_MARKETING,3600) == 0)
    else:
      logger.error('Invalid notification priority level! Assuming corrupted data for notification: %s' % notification_object)

    return False # for invalid stuff, assume it's bad
