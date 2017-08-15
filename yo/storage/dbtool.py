""" Utilities for working with SQLAlchemy databases
"""

from contextlib import contextmanager

# TODO - make this do the right thing with aiomysql

@contextmanager
def acquire_db_conn(db):
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()
