"""Full flow tests (blockchain op to transport)

   Basic idea is to setup yo's different components but not follow the real blockchain

"""

import pytest
import json
from yo import blockchain_follower
from yo import notification_sender
from yo import api_server
from yo.transports import base_transport

class MockApp:
   def __init__(self,db):
       self.db = db

class MockTransport(base_transport.BaseTransport):
   def __init__(self):
       self.received_by_user = {}
   def send_notification(self,to_subdata=None,to_username=None,notify_type=None,data=None):
       seld.received_by_user[to_username] = (to_subdata,notify_type,data)

async def test_vote_flow(sqlite_db):
    """Tests vote events get through to a transport
    """
    mock_vote_op = {'op':('vote',{'permlink':'test-post',
                                  'author'  :'testupvoted',
                                  'voter'   :'testupvoter',
                                  'weight'  :10000})}

    # boilerplate stuff
    yo_db    = sqlite_db    
    yo_app   = MockApp(yo_db)
    sender   = notification_sender.YoNotificationSender(db=yo_db,yo_app=yo_app)
    mock_tx  = MockTransport()
    sender.configured_transports['mock'] = mock_tx
    API      = api_server.YoAPIServer()
    follower = blockchain_follower.YoBlockchainFollower(db=yo_db,yo_app=yo_app)

    # configure testupvoted and testupvoter users to use mock transport for votes
    transports = {'mock':{'notification_types':['vote'],'sub_data':''}}
    await API.api_set_user_transports(username='testupvoted',transports=transports,context=dict(yo_db=sqlite_db))
    await API.api_set_user_transports(username='testupvoter',transports=transports,context=dict(yo_db=sqlite_db))

    # handle the mock vote op
    follower.notify(mock_vote_op)

    # since we don't run stuff in the background in test suite, manually invoke the notification sender
    await sender.api_trigger_notifications()

    # test it got through to our mock transport for testupvoted only
    assert 'testupvoted' in mock_tx.received_by_user.keys()
    assert not ('testupvoter' in mock_tx.received_by_user.keys())

async def test_follow_flow():
    """Tests follow events get throught to a transport
    """
    assert False # dummy

async def test_send_flow():
    """Tests send events get through to a transport
    """
    assert False

async def test_receive_flow():
    """Tests receive events get through to a transport
    """
    assert False

async def test_mention():
    """Tests mention events get through to a transport
    """
    assert False

async def test_comment():
    """Tests comment events (comment on post) get through to a transport
    """
    assert False

async def test_reply():
    """Tests reply events (replies to comments) get through to a transport
    """
    assert False
