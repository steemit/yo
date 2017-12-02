# -*- coding: utf-8 -*-
import configparser
import os

import py_vapid


class YoConfigManager:
    """A class for handling configuration details all in one place

   Also handles generation of missing keys where this is appropriate to do so
   """

    def __init__(self, filename, defaults=None):
        defaults = defaults or {}
        self.config_data = configparser.ConfigParser(
            inline_comment_prefixes=';')

        self.config_data['vapid'] = {}
        self.config_data['blockchain_follower'] = {}
        self.config_data['notification_sender'] = {}
        self.config_data['api_server'] = {}
        self.vapid_priv_key = None
        self.vapid = None
        for k, v in defaults.items():  # load defaults passed as param
            self.config_data[k] = v

        if filename:
            self.config_data.read(filename)

        for section in self.config_data.sections():
            for k in self.config_data[section]:
                if section.startswith('yo_'):
                    env_name = k.upper()
                else:
                    env_name = 'YO_%s_%s' % (section.upper(), k.upper())
                if not os.getenv(env_name) is None:
                    self.config_data[section][k] = os.getenv(env_name)
        try:
            self.log_level = os.environ.get('LOG_LEVEL',
                                            self.config_data['logging'].get(
                                                'log_level', 'INFO'))
        except BaseException:
            self.log_level = 'INFO'

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
            if not self.vapid_priv_key:
                self.vapid = py_vapid.Vapid()
                self.vapid.generate_keys()
            else:
                self.vapid = py_vapid.Vapid.from_raw(
                    private_raw=self.vapid_priv_key.encode())
