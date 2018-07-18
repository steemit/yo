# Yo notification service

Yo is a notifications service for the Steem blockchain, it streams events from the blockchain and searches them for events.

## Yo components:

Yo consists of the following components:

 1. ***Database layer***

    By default, Yo makes use of sqlite for development work and provides a simple way to implement standard test data at startup. MySQL support is the intended final use in production. This tracks user preferences and actual notifications (which are flagged as processed, mark_sent, shown and read). Each layer above the DB layer may be run distributed for reliability purposes, so long as the database supports transactions.

 2. ***Blockchain follower***

    This component follows the blockchain operations up to latest irreversible block and checks for events, sending events to the Yo notification sender for processing based on user preferences. This is done by simply inserting into the database as unprocessed and then alerting the notification sender. New event notifications are marked as processed before being dispatched to the notification sender.

    The communication between this component and the notification sender is via an internal API that should be treated as a black box by external users.

 3. ***Notification sender***

    This component handles sending out notifications to end users based on the current configuration in the database. After sending out a notification, the notification sender will mark it as mark_sent at this stage. This is where the actual notification is mark_sent to the user and for applications such as webpush an external endpoint is provided here.

 4. ***API server***

    This component is used by end users to configure their notification preferences and should be exposed as a public endpoint. API methods are exposed here to end users based on configuration (what components of Yo are in use on the particular installation).

## Installation and deployment

By default, Yo will run a node with ALL components available and will use sqlite as the database layer. Keys for third-party services and the database layer can also be specified in environment variables.

See yo.cfg for details on the environment variables used (when specified, these will override the contents of yo.cfg).


A Dockerfile is also provided for building and running yo inside a docker container, as well as a simple tool that creates a docker env file for use with the docker container by pulling values from yo.cfg.
Copy yo.cfg into my-yo.cfg or similar and then do the following:
```
make docker-image
YO_CONFIG=my-yo.cfg make .env
docker run -ti steemit/yo:latest
```


## # Yo JSON-RPC API

Calls related to notifications via [Jussi](https://github.com/steemit/jussi).

## About the different notification types

These are the notification types:

* `account_update`
* `comment_reply`
* `feed`
* `follow`
* `mention`
* `post_reply`
* `power_down`
* `send`
* `receive`
* `resteem`
* `reward`
* `vote`

All notification types share the same basic structure:

```js
        {
            "notify_id": 39,
            "notify_type": "power_down",
            "created": "2017-10-27T01:31:29.382749",
            "updated": "2017-10-27T15:16:06.178975",
            "read": true,
            "shown": false,
            "username": "test_user",
            "data": {
                "author": "roadscape",
                "amount": 10000.2
            }
        }
```

The types differ in the `data` property.

How are the types different? TODO

## JSON-RPC endpoint [/]

### Get notifications [POST]
Get a user's notifications, with filters & limit.

+ Request (application/json)

```js
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "yo.get_notifications",
            "params": {
                "username": "money", // required
                "created_before": "2017-10-27T02:38:29.906376",
                "updated_after": "2017-10-27T02:38:29.906376",
                "read": false,
                "notify_types": [
                    "comment_reply",
                    "post_reply",
                    "vote",
                    "resteem"
                ],
                "limit": 30, // defaults to 30
            }
        }
```

+ Response 200 (application/json)


```js
        {
            "jsonrpc": "2.0",
            "id": 1,
            "result": [
                {
                    "notify_id": 1,
                    "notify_type": "account_update",
                    "created": "2017-10-27T01:31:29.382749",
                    "updated": "2017-10-27T01:31:29.382749",
                    "read": false,
                    "shown": false,
                    "username": "theoretical",
                    "data": {
                      "json_metadata": "",
                      "account": "theoretical",
                      "memo_key": "STM6FATHLohxTN8RWWkU9ZZwVywXo6MEDjHHui1jEBYkG2tTdvMYo",
                      "posting": {
                        "key_auths": [
                          [
                            "STM6FATHLohxTN8RWWkU9ZZwVywXo6MEDjHHui1jEBYkG2tTdvMYo",
                            1
                          ],
                          [
                            "STM76EQNV2RTA6yF9TnBvGSV71mW7eW36MM7XQp24JxdoArTfKA76",
                            1
                          ]
                        ],
                        "account_auths": [],
                        "weight_threshold": 1
                      }
                    }
                },
                {
                    "notify_id": 2,
                    "notify_type": "comment_reply",
                    "created": "2017-10-27T01:15:29.383842",
                    "updated": "2017-10-27T01:15:29.383842",
                    "read": false,
                    "shown": false,
                    "username": "steemit",
                    "data": {
                          "title": "Welcome to Steem Reply",
                          "parent_permlink": "firstpost-reply",
                          "permlink": "firstpost-reply-comment",
                          "parent_author": "steemit",
                          "body": "I agree!",
                          "json_metadata": "",
                          "author": "steemit"
                    }
                },
                {
                    "notify_id": 3,
                    "notify_type": "feed",
                    "created": "2017-10-27T01:15:29.383842",
                    "updated": "2017-10-27T01:15:29.383842",
                    "read": false,
                    "shown": false,
                    "username": "test_user",
                    "data": {}

                },
                {
                    "notify_id": 4,
                    "notify_type": "follow",
                    "created": "2017-10-27T01:15:29.383842",
                    "updated": "2017-10-27T01:15:29.383842",
                    "read": false,
                    "shown": false,
                    "username": "steemit",
                    "data": {
                      "required_auths": [],
                      "id": "follow",
                      "json": "{\"follower\":\"steemit\",\"following\":\"steem\",\"what\":[\"posts\"]}",
                      "required_posting_auths": [
                        "steemit"
                      ]
                    }
                },
                {
                    "notify_id": 5,
                    "notify_type": "mention",
                    "created": "2017-10-27T01:15:29.383842",
                    "updated": "2017-10-27T01:15:29.383842",
                    "read": false,
                    "shown": false,
                    "username": "test_user",
                    "data": {
                          "title": "Welcome to Steem!",
                          "parent_permlink": "meta",
                          "permlink": "firstpost",
                          "parent_author": "steemit",
                          "body": "Steemit is a social media platform where anyone can earn STEEM points by posting, even @test_user.",
                          "json_metadata": "",
                          "author": "steemit"
                    }
                },
                {
                    "notify_id": 6,
                    "notify_type": "post_reply",
                    "created": "2017-10-27T01:15:29.383842",
                    "updated": "2017-10-27T01:15:29.383842",
                    "read": false,
                    "shown": false,
                    "username": "steemit",
                    "data": {
                          "title": "Welcome to Steem Reply",
                          "parent_permlink": "firstpost",
                          "permlink": "firstpost-reply",
                          "parent_author": "steemit",
                          "body": "Sounds great!",
                          "json_metadata": "",
                          "author": "steemit"
                    }
                },
                {
                    "notify_id": 7,
                    "notify_type": "power_down",
                    "created": "2017-10-27T01:15:29.383842",
                    "updated": "2017-10-27T01:15:29.383842",
                    "read": false,
                    "shown": false,
                    "username": "steemit",
                    "data": {
                      "vesting_shares": "200000.000000 VESTS",
                      "account": "steemit"
                    }
                },
                {
                    "notify_id": 8,
                    "notify_type": "send",
                    "created": "2017-10-27T01:15:29.383842",
                    "updated": "2017-10-27T01:15:29.383842",
                    "read": false,
                    "shown": false,
                    "username": "admin",
                    "data": {
                      "amount": "833.000 STEEM",
                      "from": "admin",
                      "to": "steemit",
                      "memo": ""
                    }
                },
                {
                    "notify_id": 9,
                    "notify_type": "receive",
                    "created": "2017-10-27T01:15:29.383842",
                    "updated": "2017-10-27T01:15:29.383842",
                    "read": false,
                    "shown": false,
                    "username": "steemit",
                    "data": {
                      "amount": "833.000 STEEM",
                      "from": "admin",
                      "to": "steemit",
                      "memo": ""
                    }
                },
                {
                    "notify_id": 10,
                    "notify_type": "resteem",
                    "created": "2017-10-27T01:15:29.383842",
                    "updated": "2017-10-27T01:15:29.383842",
                    "read": false,
                    "shown": false,
                    "username": "test_user",
                    "data": {}

                },
                {
                    "notify_id": 11,
                    "notify_type": "reward",
                    "created": "2017-10-27T01:15:29.383842",
                    "updated": "2017-10-27T01:15:29.383842",
                    "read": false,
                    "shown": false,
                    "username": "ivelina89",
                    "data": {
                        "author": "ivelina89",
                        "permlink": "friends-forever",
                        "sbd_payout": "2.865 SBD",
                        "steem_payout": "0.000 STEEM",
                        "vesting_payout": "1365.457442 VESTS"
                    }
                },
                {
                    "notify_id": 12,
                    "notify_type": "vote",
                    "created": "2017-10-27T01:15:29.383842",
                    "updated": "2017-10-27T01:15:29.383842",
                    "read": false,
                    "shown": false,
                    "username": "steemit78",
                    "data": {
                      "voter": "steemit78",
                      "permlink": "firstpost",
                      "author": "steemit",
                      "weight": 10000
                    }
                }
            ]
        }
```

### Mark notifications as read [POST]

```js
+ Request (application/json)

        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "yo.mark_read",
            "params": {
                "ids": [39, 10]
            }
        }
```

+ Response 200 (application/json)

```js
        {
            "jsonrpc": "2.0",
            "result": [True, True],
            "id": 1
        }
```

### Mark notifications as unread [POST]

+ Request (application/json)

```js
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "yo.mark_unread",
            "params": {
                "ids": [39, 10]
            }
        }
```

+ Response 200 (application/json)

```js
        {
            "jsonrpc": "2.0",
            "result": [True, True],
            "id": 1
        }
```

### Mark notifications as shown [POST]

+ Request (application/json)

```js
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "yo.mark_shown",
            "params": {
                "ids": [39, 10]
            }
        }
```

+ Response 200 (application/json)

```js
        {
            "jsonrpc": "2.0",
            "result": [True, True],
            "id": 1
        }
```

### Mark notifications as unshown [POST]

+ Request (application/json)

```js
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "yo.mark_unshown",
            "params": {
                "ids": [39, 10]
            }
        }
```

+ Response 200 (application/json)

```js
        {
            "jsonrpc": "2.0",
            "result": [True, True],
            "id": 1
        }
```

### Get transport configuration [POST]

+ Request (application/json)

```js
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "yo.get_transports",
            "params": {
                "username": "money"
            }
        }
```

+ Response 200 (application/json)

```js
        {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "email": {
                    "notification_types": [
                        "power_down",
                        "power_up",
                        "resteem",
                        "feed",
                        "reward",
                        "send",
                        "mention",
                        "follow",
                        "vote",
                        "comment_reply",
                        "post_reply",
                        "account_update",
                        "message",
                        "receive"
                    ]
                },
                "desktop": {
                    "notification_types": [
                        "power_down",
                        "power_up",
                        "resteem",
                        "feed",
                        "reward",
                        "send",
                        "mention",
                        "follow",
                        "vote",
                        "comment_reply",
                        "post_reply",
                        "account_update",
                        "message",
                        "receive"
                    ]
                }
            }
        }
```

### Set transport configuration [POST]

+ Request (application/json)

```js
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "yo.set_transports",
            "params": {
                "username": "money",
                "transports": {
                    "email": {
                        "notification_types": [
                            "account_update",
                            "power_down",
                            "security_new_mobile_device",
                            "security_withdrawal",
                            "security_password_changed",
                            "receive",
                            "reward",
                            "send",
                            "post_reply",
                            "comment_reply",
                            "mention",
                            "resteem",
                            "feed"
                        ]
                    },
                    "condenser": {
                        "notification_types": [
                            "account_update",
                            "power_down",
                            "security_new_mobile_device",
                            "security_withdrawal",
                            "security_password_changed",
                            "receive",
                            "reward",
                            "send",
                            "comment_reply",
                            "mention",
                            "resteem",
                            "feed"
                        ]
                    }
                }
            }
        }
```

+ Response 200 (application/json)

```js
        {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "email": {
                    "notification_types": [
                        "account_update",
                        "power_down",
                        "security_new_mobile_device",
                        "security_withdrawal",
                        "security_password_changed",
                        "receive",
                        "reward",
                        "send",
                        "post_reply",
                        "comment_reply",
                        "mention",
                        "resteem",
                        "feed"
                    ]
                },
                "condenser": {
                    "notification_types": [
                        "account_update",
                        "power_down",
                        "security_new_mobile_device",
                        "security_withdrawal",
                        "security_password_changed",
                        "receive",
                        "reward",
                        "send",
                        "comment_reply",
                        "mention",
                        "resteem",
                        "feed"
                    ]
                }
            }
        }
```


### Generic error response [POST]
How do errors look, in general? TODO

+ Request (application/json)

```js
        {
        }
```

+ Response 400 (application/json)

```js
        {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": "???",
                "message": "errors here?",
                "data" {
                    "more": "info"
                }
            }
        }
```
