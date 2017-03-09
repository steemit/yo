# yo
Modular event-driven notification service

- Accepts events via json-rpc endpoint
- Pluggable delivery architecture which will initially know how to deliver notifications via:
  - Email
  - SMS
  - Chrome Browser
- Stores all sent notifications in database
- Implements simple rate-limiting
