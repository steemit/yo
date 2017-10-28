# coding=utf-8
""" Base class for other services
"""


class YoBaseService:
    api_methods = {}
    private_api_methods = {}
    service_name = 'base'

    def __init__(self, yo_app=None, config=None, db=None):
        self.yo_app = yo_app
        self.config = config
        self.db = db

    def init_api(self, yo_app):
        pass  # pragma: no cover

    def get_name(self):
        return self.service_name  # pragma: no cover

    async def async_task(self, yo_app):  # pragma: no cover
        """ This method will run in the background
       """
        return
