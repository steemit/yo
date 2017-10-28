# coding=utf-8
import os
import configparser
import py_vapid

import logging


class YoConfigManager:
    """A class for handling configuration details all in one place

   Also handles generation of missing keys where this is appropriate to do so
   """

    def __init__(self, filename, defaults=None):
        defaults = defaults or {}
        self.config_data = configparser.ConfigParser(
            inline_comment_prefixes=';')
        # a couple of defaults to enable stuff to work-ish if the config file is missing
        # TODO - add a general get method with defaults so we don't have to define it all in multiple places
        self.config_data['yo_general'] = {'log_level': 'INFO', 'yo_db_url': ''}
        self.config_data['vapid'] = {}
        self.config_data['blockchain_follower'] = {}
        self.config_data['notification_sender'] = {}
        self.config_data['api_server'] = {}


        for k, v in defaults.items():  # load defaults passed as param
            self.config_data[k] = v

        if not (filename is None):
            self.config_data.read(filename)

        for section in self.config_data.sections():
            for k in self.config_data[section]:
                if section.startswith('yo_'):
                    env_name = k.upper()
                else:
                    env_name = 'YO_%s_%s' % (section.upper(), k.upper())
                if not os.getenv(env_name) is None:
                    self.config_data[section][k] = os.getenv(env_name)

        log_level = self.config_data['yo_general'].get('log_level', 'INFO')
        logging.basicConfig(level=log_level)
        self.generate_needed()


    def get_listen_host(self):
        return self.config_data['http'].get('listen_host',
                                            '0.0.0.0')  # pragma: no cover

    def get_listen_port(self):
        return int(self.config_data['http'].get('listen_port',
                                                8080))  # pragma: no cover


    def generate_needed(self):
        """If needed, regenerates VAPID keys and similar
       """
        self.vapid_priv_key = self.config_data['vapid'].get('priv_key', None)
        if self.vapid_priv_key is None:
            self.vapid = py_vapid.Vapid()
            self.vapid.generate_keys()
        else:
            if len(self.vapid_priv_key) == 0:
                self.vapid = py_vapid.Vapid()
                self.vapid.generate_keys()
            else:
                self.vapid = py_vapid.Vapid.from_raw(
                    private_raw=self.vapid_priv_key.encode())
