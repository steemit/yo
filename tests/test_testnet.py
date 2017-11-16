import requests
import uuid

import steem
import steembase
from steem.blockchain import Blockchain
steembase.chains.known_chains['STEEM'] = {
     'chain_id': '79276aea5d4877d9a25892eaa01b0adf019d3e5cb12a97478df3298ccdd01673',
     'prefix': 'STX', 'steem_symbol': 'STEEM', 'sbd_symbol': 'SBD', 'vests_symbol': 'VESTS'
}

class SteemTestnetUser:
   def __init__(self,generate=True,username=None,password=None):
       """If generate is set to False, username and password fields are set to those specified
          Caller is responsible for ensuring the username and password are correct

          If generate is set to True, username and password fields are ignored (new ones are generated)
       """
       if generate:
          generated = False
          while not generated:
             self.username = 'yotest%s' % str(uuid.uuid4())[:8]
             self.password = str(uuid.uuid4())
             r = requests.post('https://testnet.steem.vc/create',data={'username':self.username,'password':self.password})
             if r.status_code == 200:
                generated = True
       else:
          self.username = username
          self.password = password
       self.client = steem.Steem(['https://testnet.steem.vc'])
       self.posting_key = steembase.account.PasswordKey(self.username, self.password, role="posting")


