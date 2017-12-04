# -*- coding: utf-8 -*-

import asynctest
from yo import config
from yo.services.registration import ServiceState


class MockApp:
    def __init__(self, db):
        self.db = db
        self.config = config.YoConfigManager(None)


def test_class_variables():
    from yo.services.base_service import YoBaseService
    assert YoBaseService.service_name == 'base'


def test_instantiation(mocker):
    from yo.services.blockchain_follower import YoBlockchainFollower

    ya = MockApp(None)
    mocker.patch.object(YoBlockchainFollower, 'init_api')
    y = YoBlockchainFollower(yo_app=ya, config=None, db=None)
    assert y.service_status == ServiceState.DISABLED
    assert y.service_id is None
    assert y.service_extra == {}
    assert y.scheduler is None
    assert y.heartbeat_status == ServiceState.ENABLED
    assert y.heartbeat_interval == 10
    assert y.service_interval == 1
