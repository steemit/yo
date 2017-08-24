import jsonrpcclient

from jsonrpcclient.http_client import HTTPClient

from jsonrpcclient.request import Request

import getpass
import pprint
import yo
import logging
from yo import jsonrpc_auth

username = 'garethnelsonuk'
pubkey   = 'STM6vKTPia86DPtozntiP2YvtaqZsnz648eQmcJs9bhd6dquYY6T7'

def test_update_userprefs(wif):
    client = HTTPClient('http://localhost:8080')
    req = Request('yo.enable_transports',username=username,transports={'vote':[('email','gareth@steemit.com')]})
    canon_req,hex_sig,wif = jsonrpc_auth.sign_request(req,wif,pubkey)
    print('Canon request sent:')
    pprint.pprint(canon_req)
    results = client.send(canon_req)

    print('Server response:')
    pprint.pprint(results)

if __name__=='__main__':
   logging.basicConfig(level=logging.DEBUG)
   wif = getpass.getpass('Enter posting key WIF for %s: ' % pubkey)
   test_update_userprefs(wif)
