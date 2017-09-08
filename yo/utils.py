
# the below is a dummy until jsonrpc-auth is proper
def needs_auth(func):
    """Decorator to make sure the request is authorised on JSON-RPC calls"""
    def func_wrapper(*args,**kwargs):
        return func(*args,**kwargs) # for now we just auth everything
        if 'skip_auth' in kwargs.keys(): # pragma: no branch
           if kwargs['skip_auth']: return func(*args,**kwargs)
        if not 'username' in kwargs.keys():
           return {'error':'Could not authenticate request, missing username parameter','status':'error','error_type':'MISSING_ARGS'}
        if not 'orig_req' in kwargs.keys():
           return {'error':'Could not authenticate request, internal error','status':'error','error_type':'INTERNAL'} # we don't want to leak info here
        if not (type(kwargs['orig_req']) is dict):
           return {'error':'Could not authenticate request, request is malformed, must be a dictionary','status':'error','error_type':'MALFORMED_REQUEST'}
        if not 'params' in kwargs['orig_req'].keys():
           return {'error':'Could not authenticate request, request is malformed, lacking params','status':'error','error_type':'MALFORMED_REQUEST'}
#        if not jsonrpc_auth.verify_request(kwargs['orig_req'],kwargs['username']):
#           return {'error':'Could not authenticate request, invalid credentials','status':'error','error_type':'INVALID_CREDENTIALS'}
#        else:
#           return func(*args,**kwargs) # pragma: no cover
    return func_wrapper
