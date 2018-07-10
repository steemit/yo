# -*- coding: utf-8 -*-
import asyncio
import argparse
import os

import click
import uvloop



asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

def main():
    parser = argparse.ArgumentParser(description="Yo Notification Service")
    parser.add_argument(
        '--database_url', default=os.environ.get('DATABASE_URL', 'sqlite://'))
    subparsers = parser.add_subparsers(title='services')

    api_server_parser = subparsers.add_parser('api-server')
    api_server_parser.add_argument(
        '--http_host', type=int, default=os.environ.get('HTTP_HOST', 8080))
    api_server_parser.add_argument(
        '--http_port', type=int, default=os.environ.get('HTTP_PORT', 8080))



if __name__ == '__main__':
    main()
