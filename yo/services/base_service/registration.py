# -*- coding: utf-8 -*-
""" Base class for other services
"""
import enum
from typing import NamedTuple

import ujson


class ServiceState(enum.IntEnum):
    DISABLED = 0
    ENABLED = 1


class Registration(NamedTuple):
    service_name: str
    service_status: ServiceState
    service_id: str
    service_extra: dict = dict()

    @classmethod
    def from_row(cls, row):
        return Registration(
            service_name=row['service_name'],
            service_id=row['service_id'],
            service_status=row['service_status'],
            service_extra=row['service_extra'])

    # pylint: disable=no-member
    def asdict(self):
        return dict(self._asdict())

    def __repr__(self):
        return str(self.asdict())

    def __str__(self):
        return ujson.dumps(self._asdict())
