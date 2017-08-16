#!/bin/sh

# Sends a browser notification
# Params are simple: pass it a user ID and a string

pipenv run python3 yo/utils/simple_client.py -m send_browser_notification -p $1 msg $2
