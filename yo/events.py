# -*- coding: utf-8 -*-
'''
# namespaces
- chain
  - block
    - publish
  - op
    - <optype>
      - publish
      - field
        - <field_name>
          - equals
            - <string>
          - contains
            - <string>
- http
  - <steemit_event_name>

{ "path": "chain.op.comment.field.body.contains.@"}
{ "path" : "chain.op.comment.field.body",
  "
"event": {
            "type": "object",
            "required": [ "path" ],
            "properties": {
                "path": {
                    "type": "string
                },
                "regex": {
                    "type" : "string"
                }

            }
        }
"chain" {
    "type": "object",
    "required" : ["selector"],
    "properties": {
        "selector":  "enum": ["block","op" ]
    }
"chain.block": {
    "type": "object",
    "properties": {
        "selector": "enum": ["publish"]
    }
}
"chain.block.op": {
    "type": "object",
    "properties": {
        "selector": <optypes>
    }

}

chain.block.<optype> {


chain.block.publish
chain.op.<optype>.publish


# mentions
chain.op.comment.field.body.contains.@

chain.op.account_update.publish
chain.op.transfer_to_savings_operation
chain.op.transfer_from_savings_operation

# followers
chain.op.custom_json.field.id.equals.follow

# new block
chain.block.publish

"event" {
    "type": "object",
    "properties": {
        "occured_at": {
            "type": "datetime"
        },
        "received_at": {
            "type": "datetime"
        },
        "source": {
            "type": "string"
        },
        "data": {
            "type": "object"
        }
}

"selector" : {
    "type": "object",
    "properties": {
        "source":

'''

SOURCES = set([
    b'chain.get_dynamic_global_properties',
    b'chain.block',
    b'chain.op',
    b'chain.op.virtual'
])

SELECTORS = set([
    'key',
    'field'
])

FILTERS = ([
    'eq',
    'contains',
])



class EventSource(object):
    '''

    selector predicate: <SELECTOR>.<SUBJECT>
    filtered predicate: <SELECTOR>.<SUBJECT>.<FILTER>.<OBJECT>

    <SOURCE>.<SELECTOR_PREDICATE>
    <SOURCE>.<FILTERED_PREDICATE>


    '''

    def __init__(self):
        pass

    @classmethod
    def from_path(cls, path):
        parts = tuple(path.split('.'))

class Event(object):
    def __init__(self,*, selector_path=None, selector_func=None):
        pass

