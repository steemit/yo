#!/bin/sh

# Sends an email message
# Params are simple: pass it a destination user ID, a from username and a message

pipenv run python3 yo/utils/simple_client.py -s http://localhost:9000 -m send_email_message -p $1 $2 "$3"
