# yo
Modular event-driven notification service

- Accepts events via json-rpc endpoint
- Pluggable delivery architecture which will initially know how to deliver notifications via:
  - Email
  - SMS
  - Chrome Browser
- Stores all sent notifications in database
- Implements simple rate-limiting

Quickstart testing:

 1. Start with one of the makefile targets (for dev use make run-without-docker and set the LOG_LEVEL environment variable to DEBUG)
 2. Run "scripts/create_test_user.sh" to create a test user account
 3. Run an SSL reverse proxy
 4. Navigate to https://yourserver/gcm and follow the instructions
