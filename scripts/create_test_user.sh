#!/bin/sh

# Does what it says on the tin - creates a test user

pipenv run python3 yo/utils/simple_client.py -s http://localhost:9000 -m create_user -p testuser test@example.com Test User 666
pipenv run python3 yo/utils/simple_client.py -s http://localhost:9000 -m create_email_subscription -p 1 test@example.com
