
from yo import utils
from unittest import mock

def test_missing_params():
    """Test needs_auth() with missing params"""
    tested_func = utils.needs_auth(lambda x: None)
    retval = tested_func()
    assert retval != None
    assert retval['status']=='error'
    assert retval['error_type']=='MISSING_ARGS'
    retval = tested_func(username='testuser')
    assert retval != None
    assert retval['status']=='error'
    assert retval['error_type']=='INTERNAL'

def test_bad_req():
    """Test needs_auth() with a bad request"""
    tested_func = utils.needs_auth(lambda x: None)
    retval = tested_func(username='testuser',orig_req='') # not a valid request because it's an empty string, not a dict
    assert retval != None
    assert retval['status']=='error'
    assert retval['error_type']=='MALFORMED_REQUEST'
    retval = tested_func(username='testuser',orig_req={}) # not valid as it's not actually a JSON-RPC request and lacks the params
    assert retval != None
    assert retval['status']=='error'
    assert retval['error_type']=='MALFORMED_REQUEST'

