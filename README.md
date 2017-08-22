# Yo notification service

Yo is a notifications service for the Steem blockchain, it streams events from the blockchain and searches them for events.

## Yo components:

Yo consists of the following components:
 
 1. ***Database layer***
 
    By default, Yo makes use of sqlite for development work and provides a simple way to implement standard test data at startup. MySQL support is the intended final use in production. This tracks user preferences and actual notifications (which are flagged as processed, sent, seen and read). Each layer above the DB layer may be run distributed for reliability purposes, so long as the database supports transactions.
 
 2. ***Blockchain follower***
    
    This component follows the blockchain operations up to latest irreversible block and checks for events, sending events to the Yo notification sender for processing based on user preferences. This is done by simply inserting into the database as unprocessed and then alerting the notification sender. New event notifications are marked as processed before being dispatched to the notification sender.
    
    The communication between this component and the notification sender is via an internal API that should be treated as a black box by external users.
    
 3. ***Notification sender***
    
    This component handles sending out notifications to end users based on the current configuration in the database. After sending out a notification, the notification sender will mark it as sent at this stage. This is where the actual notification is sent to the user and for applications such as webpush an external endpoint is provided here.
    
 4. ***API server***

    This component is used by end users to configure their notification preferences and should be exposed as a public endpoint. API methods are exposed here to end users based on configuration (what components of Yo are in use on the particular installation).

## Installation and deployment

By default, Yo will run a node with ALL components available and will use sqlite as the database layer. Keys for third-party services and the database layer can also be specified in environment variables.

See yo.cfg for details on the environment variables used (when specified, these will override the contents of yo.cfg).

You should probably make use of pipenv to run yo cleanly, to do so use the provided makefile to configure pipenv and install all dependencies inside it first:
```
make build-without-docker
make install-pipenv
pipenv run steemyo -c /path/to/yo.cfg
```

A Dockerfile is also provided for building and running yo inside a docker container, as well as a simple tool that creates a docker env file for use with the docker container by pulling values from yo.cfg.
Copy yo.cfg into my-yo.cfg or similar and then do the following:
```
make docker-image
YO_CONFIG=my-yo.cfg make .env
docker run -ti steemit/yo:latest
```

## Yo API - Authentication

Yo's API methods sometimes require authentication, this is handled by signing the JSON-RPC request body with a user's private key and adding it to the HTTP request header in x-yo-signature. Depending on the exact API method, different keys may be required but usually for a user-facing API call the posting key from the steem blockchain is used.

   
## Yo API - methods

Please see documentation under docs/ for further information on single API methods
