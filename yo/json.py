# -*- coding: utf-8 -*-
from datetime import datetime
from functools import singledispatch
from functools import partial
from enum import IntEnum

from yo.schema import NotificationType
import rapidjson


@singledispatch
def to_serializable(val):
    """Used by default."""
    return str(val)


# noinspection PyUnresolvedReferences
@to_serializable.register(datetime)
def ts_datetime(val):
    """Used if *val* is an instance of datetime."""
    return val.isoformat()

@to_serializable.register(NotificationType)
def ts_notification_type(val):
    """Used if *val* is an instance of NotificationType."""
    return int(val.value())

@to_serializable.register(IntEnum)
def ts_intenum_type(val):
    """Used if *val* is an instance of IntEnum."""
    return int(val.value())

dumps = partial(rapidjson.dumps, default=to_serializable, ensure_ascii=False)
loads = rapidjson.loads
