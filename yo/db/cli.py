#! /usr/bin/env python
# -*- coding: utf-8 -*-

import click
import yo.yolog

@click.command(name='db')
@click.option('--database_url', envvar='DATABASE_URL')
def reset(database_url):
    from yo.db import reset_db
    reset_db(database_url)


if __name__ == "__main__":
    reset()
