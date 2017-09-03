from yo import config
from unittest import mock
import configparser

import os

source_code_path = os.path.dirname(os.path.realpath(__file__))

def test_basic_load():
    """Test we can load the config file sanely"""
    yo_config = config.YoConfigManager(source_code_path+'/../yo.cfg')
    # basically if no exceptions are thrown here, we're good

def test_defaults():
    """Test we can supply defaults and see them without loading a file"""
    yo_config = config.YoConfigManager('DOESNOTEXIST',defaults={'test_section':{'test_key':'test_val'}})
    assert yo_config.config_data['test_section'].get('test_key',None) == 'test_val'

def test_env_vars(monkeypatch):
    """Test we can override all variables in the config file with env variables"""
    # first we grab the defaults by loading the config file and throwing away the config manager
    config_data = config.YoConfigManager(source_code_path+'/../yo.cfg').config_data
    # now we just iterate through and make sure we can override every default with the environment
    for section in config_data.sections():
        for k in config_data[section]:
            if section.startswith('yo_'):
               env_name = k.upper()
            else:
               env_name = 'YO_%s_%s' % (section.upper(),k.upper())

            monkeypatch.setenv(env_name,1337)
            yo_config = config.YoConfigManager(source_code_path+'/../yo.cfg')
            assert int(yo_config.config_data[section].get(k))==1337

def test_file_missing():
    """Test it works when yo.cfg is missing"""
    yo_config = config.YoConfigManager('DOESNOTEXIST')
