# coding=utf-8
""" Base class for other services
"""
from abc import ABC
from abc import abstractmethod


class YoBaseService(ABC):
    api_methods = {}
    private_api_methods = {}
    service_name = 'base'

    def __init__(self, yo_app=None, config=None, db=None):
        self.yo_app = yo_app
        self.config = config
        self.db = db

    def get_name(self):
        return self.service_name

    @abstractmethod
    def init_api(self):
        pass
