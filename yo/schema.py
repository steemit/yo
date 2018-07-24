# coding=utf-8
from enum import IntEnum

class NotificationType(IntEnum):
    power_down = 1
    power_up = 2
    resteem = 3
    feed = 4
    reward = 5
    send = 6
    mention = 7
    follow = 8
    vote = 9
    comment_reply = 10
    post_reply = 11
    account_update = 12
    message = 13
    receive = 14


class TransportType(IntEnum):
    desktop = 1
    email = 2
    sms = 3


class Priority(IntEnum):
    low = 1
    normal = 2
    high = 3
    always = 4


class ActionStatus(IntEnum):
    sent = 1
    rate_limited = 2
    failed = 3
    perm_failed = 4


class EventOrigin(IntEnum):
    blockchain = 1
    steemit = 2

class EventPriority(IntEnum):
    blockchain = 1
    steemit = 2

NOTIFICATION_TYPES = [i.name for i in NotificationType]
TRANSPORT_TYPES = [i.name for i in TransportType]
EVENT_ORIGINS = [i.name for i in EventOrigin]
EVENT_PRIORITIES = [i.name for i in EventPriority]



'''
Example Notification
-------
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
'''

'''


 foo://example.com:8042/over/there?name=ferret#nose
 \_/   \______________/\_________/ \_________/ \__/
  |           |            |            |        |
scheme     authority       path        query   fragment
  |   _____________________|__
 / \ /                        \
 urn:example:animal:ferret:nose



'''

'''
flow
bf detects operation
op's handlers are run to generate event

begin transaction
    event is stored
    potential notification accounts are determined
    account notification prefs are loaded
    events are filtered against notification prefs
    filtered events are added to transport queues
end transaction

transport queue item read

if not rate-limited
    load user info from conveyor
    attempt send
    if success:
        delete queue item
        record result

if rate-limited:
    delete queue item
    record result
    

'''

yo_schema = {
    '$schema': 'http://json-schema.org/draft-06/schema#',
    'id': 'https://schema.steemit.com/yo/objects.json',
    'title': 'notification transport schema',
    'definitions': {
        'transport': {
            'title': 'transport',
            'type': 'object',
            'properties':{
                'transport': {
                    '$ref': '#/definitions/transport_type'
                },
                'notification_types': {
                    "type": "array",
                    "uniqueItems": True,
                    'items': {
                        '$ref': '#/definitions/notification_type'
                    }
                },
                'data': 'object'
            },
            'required': ['transport','notification_types'],
            'additionalProperties': False,

        },
        'notification': {
            'title': 'notification schema',
            'type':'object',
            'properties': {
                'nid': 'number',
                'notify_type': {
                    '$ref': '#/definitions/notification_type'
                },
                'created': 'string',
                'to_username': 'string',
                'from_username': 'string',
                'json_data': {
                    'type':'object'
                },
                'priority': {
                    '$ref': '#/definitions/priority'
                }
            },
            'required': ['notify_id','notify_type','created','updated','read','shown','username','data'],
            'additionalProperties': False
        },
        'priority': {
            'type': 'string',
            'enum': EVENT_PRIORITIES
        },
        'notification_type': {
            'type': 'string',
            'enum': NOTIFICATION_TYPES
        },
        'transport_type': {
            'type':'string',
            'enum': TRANSPORT_TYPES
        },
        'event_origin': {
            'type': 'string',
            'enum': EVENT_ORIGINS
        },
        'event_urn': {
            'type': 'string'
        },
        'event': {
            'title': 'event schema',
            'type': 'object',
            'properties': {
                'priority': {
                    '$ref': '#/definitions/priority'
                },
                'urn': {
                    '$ref': '#/definitions/event_urn'
                },
                'origin': {
                    '$ref': '#/definitions/event_origin'
                },
                'data': {
                    'type':'object',
                }
            },
            'required': ['priority','urn','origin','data'],
            'additionalProperties': False
        }
    }
}



EVENTS = {
    'account_update': {
        'priority': 'HIGH',
        'source_event': {
            'type': 'blockchain',
            'filter': {
                'operation_type': ['account_update']
            },
            'example': {
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
        }
    },
    'comment_reply':  {
        'priority': 'LOW',
        'source_event': {
            'type': 'blockchain',
            'filter': {
                'operation_type': ['comment'],
                'parent_permlink': [{"anything-but":""}]
            },
            'example': {
                  "title": "Welcome to Steem!",
                  "parent_permlink": "meta",
                  "permlink": "firstpost",
                  "parent_author": "steemit",
                  "body": "Steemit is a social media platform where anyone can earn STEEM points by posting. The more people who like a post, the more STEEM the poster earns. Anyone can sell their STEEM for cash or vest it to boost their voting power.",
                  "json_metadata": "",
                  "author": "steemit"
            }
        }
    },
    'feed':           {
        'priority': 'LOW',
        'source_event':   {
            'type':'blockchain',
            'filter': {
                'operation_type': [],
            },
            'example':{}
        }
    },
    'follow':         {
        'priority': 'LOW',
        'source_event':   {
            'type':'blockchain',
            'filter': {
                'operation_type': ['custom_json'],
            },
            'example':{
              "required_auths": [],
              "id": "follow",
              "json": "{\"follower\":\"steemit\",\"following\":\"steem\",\"what\":[\"posts\"]}",
              "required_posting_auths": [
                "steemit"
              ]
            }
        }
    },
    'mention':        {
        'priority': 'LOW',
        'source_event':   {
            'type':'blockchain',
            'filter': {
                'operation_type': ['comment'],
            },
            'example':{
                  "title": "Welcome to Steem!",
                  "parent_permlink": "meta",
                  "permlink": "firstpost",
                  "parent_author": "steemit",
                  "body": "Steemit is a social media platform where anyone can earn STEEM points by posting. The more people who like a post, the more STEEM the poster earns. Anyone can sell their STEEM for cash or vest it to boost their voting power.",
                  "json_metadata": "",
                  "author": "steemit"
            }
        }
    },
    'post_reply':     {
        'priority': 'LOW',
        'source_event':   {
            'type':'blockchain',
            'filter': {
                'operation_type': ['comment'],
            },
            'example':{}
        }
    },
    'power_down':     {
        'priority': 'LOW',
        'source_event':   {
            'type':'blockchain',
            'filter': {
                'operation_type': ['withdraw_vesting'],
            },
            'example':{
              "vesting_shares": "200000.000000 VESTS",
              "account": "steemit"
            }
        }
    },
    'send':           {
        'priority': 'LOW',
        'source_event':   {
            'type':'blockchain',
            'filter': {
                'operation_type': ['transfer'],
            },
            'example':{
              "amount": "833.000 STEEM",
              "from": "admin",
              "to": "steemit",
              "memo": ""
            }
        }
    },
    'receive':        {
        'priority': 'LOW',
        'source_event':   {
            'type':'blockchain',
            'filter': {
                'operation_type': ['transfer'],
            },
            'example':{
              "amount": "833.000 STEEM",
              "from": "admin",
              "to": "steemit",
              "memo": ""
            }
        }
    },
    'resteem':        {
        'priority': 'LOW',
        'source_event':   {
            'type':'blockchain',
            'filter': {
                'operation_type': ['custom_json'],
            },
            'example':{}
        }
    },
    'reward':         {
        'priority': 'LOW',
        'source_event':   {
            'type':'blockchain',
            'filter': {
                'operation_type': [],
            },
            'example': {
                "author": "ivelina89",
                "permlink": "friends-forever",
                "sbd_payout": "2.865 SBD",
                "steem_payout": "0.000 STEEM",
                "vesting_payout": "1365.457442 VESTS"
            }
        }
    },
    'vote':           {
        'priority': 'LOW',
        'source_event':   {
            'type':'blockchain',
            'filter': {
                'operation_type': ['vote'],
            },
            'example':{
              "voter": "steemit78",
              "permlink": "firstpost",
              "author": "steemit",
              "weight": 10000
            }
        }
    }
}
