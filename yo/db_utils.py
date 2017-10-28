# coding=utf-8
import argparse
import json
import logging

import dateutil.parser

from .db import metadata
from .db import YoDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_db(args=None, db_url=None):
    db_url = db_url or args.db_url
    db = YoDatabase(db_url)
    logger.info('Reseting db')
    metadata.drop_all(bind=db.engine)
    logger.info('Finished wiping old data')
    metadata.create_all(bind=db.engine)
    if not args:
        return db # if called somewhere else like a test, return the db

def init_db(args=None, db_url=None, init_data=None, init_file=None, reset=False):
    if args:
        db_url =  db_url or args.db_url
        init_file = init_file or args.init_file

    logger.info('Creating/updating database schema...')

    if reset:
        db = reset_db(db_url=db_url)
    else:
        db = YoDatabase(db_url)
        metadata.create_all(bind=db.engine)

    init_data = init_data or []
    if init_file:
        logger.info('Loading initdata from file %s', init_file)
        with open(init_file, 'rb') as f:
            init_data.append(json.load(f))
            logger.info('Finished reading initdata file')

    logger.info('Inserting %d items from initdata into database...',
             len(init_data))
    with db.engine.connect() as conn:
        for table_name, data in init_data:
            for k, v in data.items():
                if str(metadata.tables['yo_%s' % table_name].columns[k]
                               .type) == 'DATETIME':
                    data[k] = dateutil.parser.parse(v)
                conn.execute(metadata.tables['yo_%s' % table_name].insert(),
                         **data)
    logger.info(
            'Finished inserting %d items from initdata' % len(init_data))

    if not args:
        return db # if called somewhere else like a test, return the db

def main():
    parser = argparse.ArgumentParser(
        description="Yo database utils")
    parser.add_argument('db_url', type=str)
    subparsers = parser.add_subparsers(help='sub-command help')
    init_sub = subparsers.add_parser('init')
    init_sub.add_argument('--init_file', type=str)
    init_sub.set_defaults(func=init_db)

    reset_sub = subparsers.add_parser('reset')
    reset_sub.set_defaults(func=reset_db)
    args = parser.parse_args()
    args.func(args=args)


if __name__ == '__main__':
    main()