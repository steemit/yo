import jsonrpcclient

from jsonrpcclient.http_client import HTTPClient

from jsonrpcclient.request import Request

import getpass
import pprint
import logging


username = 'garethnelsonuk'
pubkey   = 'STM6vKTPia86DPtozntiP2YvtaqZsnz648eQmcJs9bhd6dquYY6T7'

def test_update_userprefs():
    client = HTTPClient('http://localhost:8080')
    req = Request('yo.enable_transports',username=username,transports={'vote':['email','gareth@steemit.com']})
    print('request sent:')
    pprint.pprint(req)
    results = client.send(req)

    print('Server response:')
    pprint.pprint(results)

if __name__=='__main__':
   logging.basicConfig(level=logging.DEBUG)
   test_update_userprefs()
