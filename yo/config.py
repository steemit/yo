import os
import configparser
import py_vapid

import logging


class YoConfigManager:
   """A class for handling configuration details all in one place

   Also handles generation of missing keys where this is appropriate to do so
   """
   def __init__(self,filename):
       self.config_data = configparser.ConfigParser(inline_comment_prefixes=';')
       self.config_data.read(filename)
       
       for section in self.config_data.sections():
               for k in self.config_data[section]:
                   if section.startswith('yo_'): 
                      env_name = k.upper()
                   else:
                      env_name = 'YO_%s_%s' % (section.upper(),k.upper())
                   if not os.getenv(env_name) is None:
                          self.config_data[section][k] = os.getenv(env_name)
 
       log_level = self.config_data['yo_general'].get('log_level','INFO')
       logging.basicConfig(level=log_level)
       self.generate_needed()
       self.update_enabled()
   def get_listen_host(self):
       return self.config_data['http'].get('listen_host','0.0.0.0')
   def get_listen_port(self):
       return int(self.config_data['http'].get('listen_port',8080))
   def update_enabled(self):
       self.enabled_services = []
       if self.config_data['blockchain_follower'].get('enabled',0): self.enabled_services.append('blockchain_follower')
   def generate_needed(self):
       """If needed, regenerates VAPID keys and similar
       """
       self.vapid_priv_key = self.config_data['vapid'].get('priv_key',None)
       self.vapid = py_vapid.Vapid(private_key=self.vapid_priv_key)
       if self.vapid_priv_key is None:
          self.vapid.generate_keys()
           

