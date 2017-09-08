from yo import utils
from yo import jsonrpc_auth
from jsonrpcclient.request import Request
import json
from unittest import mock
import pytest

@pytest.mark.skip(reason="current jsonrpc-auth implementation is dummy")
def test_missing_params():
    """Test needs_auth() with missing params"""
    tested_func = utils.needs_auth(lambda x: None)
    retval = tested_func(skip_auth=False)
    assert retval != None
    assert retval['status']=='error'
    assert retval['error_type']=='MISSING_ARGS'
    retval = tested_func(username='testuser',skip_auth=False)
    assert retval != None
    assert retval['status']=='error'
    assert retval['error_type']=='INTERNAL'


@pytest.mark.skip(reason="current jsonrpc-auth implementation is dummy")
def test_skip_auth():
    @utils.needs_auth
    def tested_func(*args,**kwargs):
        return True
    retval = tested_func(skip_auth=True)
    assert retval


@pytest.mark.skip(reason="current jsonrpc-auth implementation is dummy")
def test_bad_req():
    """Test needs_auth() with a bad request"""
    tested_func = utils.needs_auth(lambda x: None)
    retval = tested_func(username='testuser',orig_req='',skip_auth=False) # not a valid request because it's an empty string, not a dict
    assert retval != None
    assert retval['status']=='error'
    assert retval['error_type']=='MALFORMED_REQUEST'
    retval = tested_func(username='testuser',orig_req={},skip_auth=False) # not valid as it's not actually a JSON-RPC request and lacks the params
    assert retval != None
    assert retval['status']=='error'
    assert retval['error_type']=='MALFORMED_REQUEST'


@pytest.mark.skip(reason="current jsonrpc-auth implementation is dummy")
def test_bad_credentials():
    """Test needs_auth() with bad credentials"""
    tested_func = utils.needs_auth(lambda x: None)
    bad_pub_key      = 'STM6sXZdPhLGrDP1MRyZ2zbhXUGNAbrS7qj1o8TFwNkzg47PRQMXK' # does not exist in the blockchain for @steemit user
    bad_priv_key     = '5JVEH3LTxHzwfwdRB9nDZG1mmFugGWWaGk4fccz1GPt4bwtXy3F'
    request          = Request('test_method',stuff=1)

    canon_req,hex_sig,wif = jsonrpc_auth.sign_request(request,bad_priv_key,bad_pub_key)
    retval = tested_func(username='steemit',orig_req=json.loads(canon_req),skip_auth=False)
    assert retval != None
    assert retval['status']=='error'
    assert retval['error_type']=='INVALID_CREDENTIALS'


