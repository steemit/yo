
import yo.json
import re

import steem
import structlog

from ...schema import Priority
from ...schema import NotificationType as Notification

logger = structlog.get_logger(__name__)


# any valid @username with a trailing whitespace
MENTION_PATTERN = re.compile(r'@([a-z][a-z0-9\-]{2,15})\s')


def eid(op):
    return f'{op["block"]}/{op["trx_in_block"]}/{op["op_in_trx"]}/{op["virtual_op"]}'

def handle_vote(op):
    vote_info = op['op'][1]
    logger.info(
        'handle_vote',
        permlink=vote_info['permlink'],
        author=vote_info['author'],
        voter=vote_info['voter'],
        weight=vote_info['weight'])

    return [
        {
             'eid':           eid(op),
             'from_username': vote_info['voter'],
             'to_username':   vote_info['author'],
             'json_data':     yo.json.dumps(vote_info),
             'notify_type':   Notification.vote,
             'priority':      Priority.low.value
        }
    ]


def handle_follow(op):
    if op['op'][1]['id'] != 'follow':
        logger.debug('handle_follow noop')
        return []

    op_data = op['op'][1]
    follow_data = yo.json.loads(op_data['json'])
    if follow_data[0] != 'follow':
        return []

    follower = follow_data[1]['follower']
    following = follow_data[1]['following']

    if len(op_data['required_posting_auths']) != 1:
        logger.error('inavlid follow op, got %d posting auths, expected 1',
                       op_data['required_posting_auths'])
        return []

    if op_data['required_posting_auths'][0] != follower:
        logger.error('invalid follow op, follower must be signer')
        return []
    logger.debug('handle_follow', follower=follower, following=following)

    return [
        {'eid':           eid(op),
         'from_username': follower,
         'to_username':   following,
         'json_data':     yo.json.dumps(follow_data[1]),
         'notify_type':   Notification.follow,
         'priority':      Priority.low.value
        }
    ]


def handle_account_update(op):
    op_data = op['op'][1]
    logger.debug('handle_account_update', account=op_data['account'])
    return [
        {'eid':         eid(op),
         'to_username': op_data['account'],
         'json_data':   yo.json.dumps(op_data),
         'notify_type': Notification.account_update,
         'priority':    Priority.low.value
        }
    ]


def handle_send(op):
    op_data = op['op'][1]
    send_data = {
        'amount': op_data['amount'],
        'from':   op_data['from'],
        'memo':   op_data['memo'],
        'to':     op_data['to'],
    }
    logger.debug(
        'handle_send',
        _from=send_data['from'],
        amount=send_data['amount'],
        to=send_data['to'])
    return [
        {'eid':         eid(op),
         'to_username': send_data['from'],
         'json_data':   yo.json.dumps(send_data),
         'notify_type': Notification.send,
         'priority':    Priority.low.value
        }
    ]


def handle_receive(op):
    op_data = op['op'][1]
    receive_data = {
        'amount': op_data['amount'],
        'from':   op_data['from'],
        'memo':   op_data['memo'],
        'to':     op_data['to'],
    }
    logger.debug(
        'handle_receive',
        to=receive_data['to'],
        amount=receive_data['amount'],
        _from=receive_data['from'])
    return [
        {'eid':           eid(op),
         'to_username':   receive_data['to'],
         'from_username': receive_data['from'],
         'json_data':     yo.json.dumps(receive_data),
         'notify_type':   Notification.receive,
         'priority':      Priority.low.value
        }
    ]


def handle_power_down(op):
    op_data = op['op'][1]
    logger.debug(
        'handle_power_down',
        account=op_data['account'],
        amount=op_data['vesting_shares'])
    return [
        {'eid':         eid(op),
         'to_username': op_data['account'],
         'json_data':   yo.json.dumps(op_data),
         'notify_type': Notification.power_down,
         'priority':    Priority.low.value
        }
    ]


def handle_mention(op):
    comment_data = op['op'][1]
    haystack = comment_data['body'] + '\n'
    data = {
        'author':   comment_data['author'],
        'permlink': comment_data['permlink'],
    }
    notifications = []
    for match in set(re.findall(MENTION_PATTERN, haystack)):
        logger.debug('handle_mention', author=data['author'], mentioned=match)
        notifications.append(
            {'eid':           eid(op),
             'to_username':   match,
             'from_username': data['author'],
             'json_data':     yo.json.dumps(data),
             'notify_type':   Notification.mention,
             'priority':      Priority.low.value
            })
    return notifications


def handle_comment(op):
    logger.debug('handle_comment', op=['op'][0])
    op_data = op['op'][1]
    if op_data['parent_author'] == '':
        # top level post
        return []
    parent_id = '@' + op_data['parent_author'] + '/' + op_data['parent_permlink']
    parent = steem.post.Post(parent_id)
    note_type = Notification.comment_reply if parent.is_comment() else Notification.post_reply
    logger.debug(
        'handle_comment',
        note_type=note_type,
        author=op_data['author'],
        parent_id=parent_id)
    return [
        {'eid':           eid(op),
         'to_username':   op_data['parent_author'],
         'from_username': op_data['author'],
         'json_data':     yo.json.dumps(op_data),
         'notify_type':   note_type,
         'priority':      Priority.low.value
        }
    ]


def handle_resteem(op):
    op_data = op['op'][1]
    resteem_data = yo.json.loads(op_data['json'])
    try:
        if resteem_data[0] != 'reblog':
            logger.debug('handle_resteem noop')
            return []
    except KeyError:
        logger.debug('handle_resteem noop')
        return []

    account = resteem_data[1]['account']
    author = resteem_data[1]['author']
    permlink = resteem_data[1]['permlink']
    if len(op_data['required_posting_auths']) != 1:
        logger.error('inavlid resteem op, got %d posting auths, expected 1',
                       op_data['required_posting_auths'])
        return []
    if op_data['required_posting_auths'][0] != account:
        logger.error('invalid resteem op, account must be signer')
        return []
    logger.debug(
        'handle_resteem', account=account, author=author, permlink=permlink)
    return [
        {'eid':           eid(op),
         'from_username': account,
         'to_username':   author,
         'json_data':     yo.json.dumps(resteem_data[1]),
         'notify_type':   Notification.resteem,
         'priority':      Priority.low.value
        }
    ]
# pylint: enable=no-member
