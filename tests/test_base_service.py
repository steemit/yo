# -*- coding: utf-8 -*-
import argparse
import asynctest

from yo.services.registration import ServiceState





def test_class_variables():
    from yo.services.base_service import YoBaseService
    assert YoBaseService.service_name == 'base'


def test_instantiation(mocker, basic_mock_app):
    from yo.services.blockchain_follower import YoBlockchainFollower

    ya = basic_mock_app
    mocker.patch.object(YoBlockchainFollower, 'init_api')
    y = YoBlockchainFollower(yo_app=ya, config=None, db=None)
    assert y.service_status == ServiceState.DISABLED
    assert y.service_id is None
    assert y.service_extra == {}
    assert y.scheduler is None
    assert y.heartbeat_status == ServiceState.ENABLED
    assert y.heartbeat_interval == 10
    assert y.service_interval == 1
