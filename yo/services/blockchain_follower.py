# -*- coding: utf-8 -*-
import asyncio
from collections import defaultdict
import itertools
import json
import re

import steem
from steem.blockchain import Blockchain
import structlog

from ..db import Priority
from .base_service import YoBaseService

logger = structlog.getLogger(__name__, service_name='blockchain_follower')

# TODO - use reliable stream when merged into steem-python

# Basically this service just follows the blockchain and inserts into the
# DB then triggers the notification sender to send the actual notification

# NOTIFICATION TYPES
ACCOUNT_UPDATE = 'account_update'
# Not a blockchain event ANNOUNCEMENT_IMPORTANT = 'announcement_important'
COMMENT_REPLY = 'comment_reply'
FEED = 'feed'
FOLLOW = 'follow'
MENTION = 'mention'
POST_REPLY = 'post_reply'
POWER_DOWN = 'power_down'
SEND_STEEM = 'send'
RECEIVE_STEEM = 'receive'
RESTEEM = 'resteem'
REWARD = 'reward'
VOTE = 'vote'

# any valid @username with a trailing whitespace
MENTION_PATTERN = re.compile(r'@([a-z][a-z0-9\-]{2,15})\s')


class YoBlockchainFollower(YoBaseService):
    service_name = 'blockchain_follower'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # init blockchain
        steemd_url = self.yo_app.config.steemd_url

        self.steemd = steem.steemd.Steemd(nodes=[steemd_url])
        self.blockchain = Blockchain(steemd_instance=self.steemd)
        self.start_block = self.yo_app.config.steemd_start_block

        self.last_block_num_handled = 0

        # init ops handlers
        self.op_map = defaultdict(list)
        self.op_map.update({
            'vote': [self.handle_vote],
            'account_update': [self.handle_account_update],
            'transfer': [self.handle_send, self.handle_receive],
            'custom_json': [self.handle_follow, self.handle_resteem],
            'withdraw_vesting': [self.handle_power_down],
            'comment': [self.handle_mention, self.handle_comment]
        })

        start_block = self.get_start_block()
        self.ops_func = self.blockchain.stream_from(
            start_block=start_block, batch_operations=True)
        self.ops = lambda: self.execute_sync(next, self.ops_func)

    def get_start_block(self):
        start_block = None
        try:
            if isinstance(self.start_block, int) and self.start_block < 0:
                start_block = self.blockchain.get_current_block_num() - self.start_block
        except Exception:
            self.log.exception('service error')
            start_block = None
        self.log.debug('get_start_block', start_block=start_block)
        return start_block

    async def store_notification(self, notifications):
        return await self.db.create_notifications(notifications)

    # pylint gets confused about these for some reason
    # pylint: disable=no-member
    async def handle_vote(self, op):
        vote_info = op['op'][1]
        self.log.info(
            'handle_vote',
            permlink=vote_info['permlink'],
            author=vote_info['author'],
            voter=vote_info['voter'],
            weight=vote_info['weight'])

        return [
            dict(
                trx_id=op['trx_id'],
                from_username=vote_info['voter'],
                to_username=vote_info['author'],
                json_data=json.dumps(vote_info),
                notify_type=VOTE,
                priority_level=Priority.LOW.value)
        ]

    async def handle_follow(self, op):
        if op['op'][1]['id'] != 'follow':
            self.log.debug('handle_follow noop')
            return []

        op_data = op['op'][1]
        follow_data = json.loads(op_data['json'])
        if follow_data[0] != 'follow':
            return []

        follower = follow_data[1]['follower']
        following = follow_data[1]['following']

        if len(op_data['required_posting_auths']) != 1:
            self.log.error('inavlid follow op, got %d posting auths, expected 1',
                           op_data['required_posting_auths'])
            return []

        if op_data['required_posting_auths'][0] != follower:
            self.log.error('invalid follow op, follower must be signer')
            return []
        self.log.debug('handle_follow', follower=follower, following=following)

        return [
            dict(
                trx_id=op['trx_id'],
                from_username=follower,
                to_username=following,
                json_data=json.dumps(follow_data[1]),
                notify_type=FOLLOW,
                priority_level=Priority.LOW.value)
        ]

    async def handle_account_update(self, op):
        op_data = op['op'][1]
        self.log.debug('handle_account_update', account=op_data['account'])
        return [
            dict(
                trx_id=op['trx_id'],
                to_username=op_data['account'],
                json_data=json.dumps(op_data),
                notify_type=ACCOUNT_UPDATE,
                priority_level=Priority.LOW.value)
        ]

    async def handle_send(self, op):
        op_data = op['op'][1]
        send_data = {
            'amount': op_data['amount'],
            'from': op_data['from'],
            'memo': op_data['memo'],
            'to': op_data['to'],
        }
        self.log.debug(
            'handle_send',
            _from=send_data['from'],
            amount=send_data['amount'],
            to=send_data['to'])
        return [
            dict(
                trx_id=op['trx_id'],
                to_username=send_data['from'],
                json_data=json.dumps(send_data),
                notify_type=SEND_STEEM,
                priority_level=Priority.LOW.value)
        ]

    async def handle_receive(self, op):
        op_data = op['op'][1]
        receive_data = {
            'amount': op_data['amount'],
            'from': op_data['from'],
            'memo': op_data['memo'],
            'to': op_data['to'],
        }
        self.log.debug(
            'handle_receive',
            to=receive_data['to'],
            amount=receive_data['amount'],
            _from=receive_data['from'])
        return [
            dict(
                trx_id=op['trx_id'],
                to_username=receive_data['to'],
                from_username=receive_data['from'],
                json_data=json.dumps(receive_data),
                notify_type=RECEIVE_STEEM,
                priority_level=Priority.LOW.value)
        ]

    async def handle_power_down(self, op):
        op_data = op['op'][1]
        self.log.debug(
            'handle_power_down',
            account=op_data['account'],
            amount=op_data['vesting_shares'])
        return [
            dict(
                trx_id=op['trx_id'],
                to_username=op_data['account'],
                json_data=json.dumps(op_data),
                notify_type=POWER_DOWN,
                priority_level=Priority.LOW.value)
        ]

    async def handle_mention(self, op):
        comment_data = op['op'][1]
        haystack = comment_data['body'] + '\n'
        data = {
            'author': comment_data['author'],
            'permlink': comment_data['permlink'],
        }
        notifications = []
        for match in set(re.findall(MENTION_PATTERN, haystack)):
            self.log.debug('handle_mention', author=data['author'], mentioned=match)
            notifications.append(
                dict(
                    trx_id=op['trx_id'],
                    to_username=match,
                    from_username=data['author'],
                    json_data=json.dumps(data),
                    notify_type=MENTION,
                    priority_level=Priority.LOW.value))
        return notifications

    async def handle_comment(self, op):
        self.log.debug('handle_comment', op=['op'][0])
        op_data = op['op'][1]
        if op_data['parent_author'] == '':
            # top level post
            return []
        parent_id = '@' + op_data['parent_author'] + '/' + op_data['parent_permlink']
        parent = steem.post.Post(parent_id)
        note_type = COMMENT_REPLY if parent.is_comment() else POST_REPLY
        self.log.debug(
            'handle_comment',
            note_type=note_type,
            author=op_data['author'],
            parent_id=parent_id)
        return [
            dict(
                trx_id=op['trx_id'],
                to_username=op_data['parent_author'],
                from_username=op_data['author'],
                json_data=json.dumps(op_data),
                notify_type=note_type,
                priority_level=Priority.LOW.value)
        ]

    async def handle_resteem(self, op):
        op_data = op['op'][1]
        resteem_data = json.loads(op_data['json'])
        if resteem_data[0] != 'reblog':
            self.log.debug('handle_resteem noop')
            return []

        account = resteem_data[1]['account']
        author = resteem_data[1]['author']
        permlink = resteem_data[1]['permlink']
        if len(op_data['required_posting_auths']) != 1:
            self.log.error('inavlid resteem op, got %d posting auths, expected 1',
                           op_data['required_posting_auths'])
            return []
        if op_data['required_posting_auths'][0] != account:
            self.log.error('invalid resteem op, account must be signer')
            return []
        self.log.debug(
            'handle_resteem', account=account, author=author, permlink=permlink)
        return [
            dict(
                trx_id=op['trx_id'],
                from_username=account,
                to_username=author,
                json_data=json.dumps(resteem_data[1]),
                notify_type=RESTEEM,
                priority_level=Priority.LOW.value)
        ]

    # pylint: enable=no-member

    async def notify(self, blockchain_op):
        """ Handle notification for a particular op
        """
        op_type = blockchain_op['op'][0]
        futures = [handler(blockchain_op) for handler in self.op_map[op_type]]
        if futures:
            self.log.debug(
                'operation triggering handlers', op_type=op_type, handlers=futures)
            return await asyncio.gather(*futures)
        else:
            self.log.debug('skipping operation', op_type=op_type)
            return []

    async def ops_iter(self):
        start_block = self.get_start_block()
        ops_func = self.blockchain.stream_from(
            start_block=start_block, batch_operations=True)
        while True:
            ops = await self.execute_sync(next, ops_func)
            yield ops

    async def main_task(self):
        self.log.debug('main task executed')
        async for ops in self.ops_iter():
            block_num = ops[0]['block']
            self.log.debug('main task', op_in_block=len(ops), block_num=block_num)

            unstored_notifications = await asyncio.gather(
                *[self.notify(op) for op in ops])
            combined_notifications = list(
                itertools.chain(*itertools.chain(*unstored_notifications)))

            logger.debug(
                'main_task',
                block_num=block_num,
                op_count=len(ops),
                unstored_count=sum(map(len, unstored_notifications)),
                combined_notifications=len(combined_notifications))
            resp = await self.store_notification(combined_notifications)
            if resp:
                self.last_block_num_handled = block_num
