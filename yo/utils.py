from yo import jsonrpc_auth 

def needs_auth(func):
    """Decorator to make sure the request is authorised on JSON-RPC calls"""
    def func_wrapper(*args,**kwargs):
        if 'skip_auth' in kwargs.keys():
           if kwargs['skip_auth']: return func(*args,**kwargs)
        if not 'username' in kwargs.keys():
           return {'error':'Could not authenticate request, missing username parameter'}
        if not 'orig_req' in kwargs.keys():
           return {'error':'Could not authenticate request, internal error'}
        if not jsonrpc_auth.verify_request(kwargs['orig_req'],kwargs['username']):
           return {'error':'Could not authenticate request, invalid credentials'}
        return func(*args,**kwargs)
    return func_wrapper
