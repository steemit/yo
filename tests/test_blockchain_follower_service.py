# -*- coding: utf-8 -*-

import asynctest
from yo import config


class MockApp:
    def __init__(self, db):
        self.db = db
        self.config = config.YoConfigManager(None)


def test_instantiation(mocker):
    from yo.services.blockchain_follower import YoBlockchainFollower

    ya = MockApp(None)
    mocker.patch.object(YoBlockchainFollower, 'init_api')
    y = YoBlockchainFollower(yo_app=ya, config=None, db=None)
    assert y.service_status == 0
    assert y.service_id is None
    assert y.service_extra == {}
