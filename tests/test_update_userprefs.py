import jsonrpcclient
import jsonrpc_auth

from jsonrpcclient.http_client import HTTPClient

from jsonrpcclient.request import Request

import getpass
import pprint

from jsonrpc_auth import AuthorizedRequest

username = 'garethnelsonuk'

def test_update_userprefs(wif):
    client = HTTPClient('http://localhost:8080')
    req = Request('yo.enable_transports',username=username,transports={'vote':[('email','gareth@steemit.com')]})
    canon_req,hex_sig,wif = AuthorizedRequest.sign_request(req,wif)
    results = client.send(canon_req)
    pprint.pprint(results)

if __name__=='__main__':
   wif = getpass.getpass('Enter posting key WIF: ')
   test_update_userprefs(wif)
