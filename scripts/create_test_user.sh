#!/bin/sh

# Does what it says on the tin - creates a test user

pipenv run python3 yo/utils/simple_client.py -m create_user -p testuser test@example.com Test User 666
