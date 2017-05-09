# coding=utf-8
import logging
import os

import sqlalchemy as sa

log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'))
logging.basicConfig(level=log_level)
logger = logging.getLogger('__name__')

metadata = sa.MetaData()