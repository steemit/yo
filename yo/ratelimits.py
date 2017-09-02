import logging
logger = logging.getLogger(__name__)

def check_ratelimit(notification_object):
    """Checks if this notification should be sent or not

    Args:
        notification_object(dict): The notification in question, must contain the priority field

    Returns:
        True if allowed, False if not
    """
    return True # dummy for now
