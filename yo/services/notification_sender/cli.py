# -*- coding: utf-8 -*-
import click
import yo.yolog

@click.command(name='sender')
@click.option('--database_url', envvar='DATABASE_URL')
def yo_noitification_sender_service(database_url):
    from yo.services.notification_sender import main_task
    main_task(database_url=database_url)

if __name__ == '__main__':
    yo_noitification_sender_service()
