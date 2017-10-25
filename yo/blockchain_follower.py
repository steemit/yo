from .base_service import YoBaseService
from .db import notifications_table, PRIORITY_LEVELS
import asyncio
import steem
from steem.blockchain import Blockchain
import json
import re

import logging

logger = logging.getLogger(__name__)

# TODO - use reliable stream when merged into steem-python

# Basically this service just follows the blockchain and inserts into the DB then triggers the notification sender to send the actual notification

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

    async def send_notification(self, **data):
        data['sent'] = False
        self.db.create_notification(**data)
        sender_response = await self.yo_app.invoke_private_api(
            'notification_sender', 'trigger_notification',
            username=data['to_username'])
        logger.debug('Got %s from notification sender' % str(sender_response))

    async def handle_vote(self, op):
        logger.debug('handle_vote received %s op' % ['op'][0])
        vote_info = op['op'][1]
        logger.debug('Vote on %s (written by %s) by %s with weight %s' % (
            vote_info['permlink'], vote_info['author'],
            vote_info['voter'], vote_info['weight']))
        await self.send_notification(trx_id=op['trx_id'],
                                     from_username=vote_info['voter'],
                                     to_username=vote_info['author'],
                                     json_data=json.dumps(vote_info),
                                     type=VOTE,
                                     priority_level=PRIORITY_LEVELS['low'])
        return True

    async def handle_follow(self, op):
        op_data = op['op'][1]
        follow_data = json.loads(op_data['json'])
        if follow_data[0] != 'follow':
            return False
        follower = follow_data[1]['follower']
        following = follow_data[1]['following']
        if len(op_data['required_posting_auths']) != 1:
            logger.error('inavlid follow op, got %d posting auths, expected 1' % op_data['required_posting_auths'])
            return False
        if op_data['required_posting_auths'][0] != follower:
            logger.error('invalid follow op, follower must be signer')
            return False
        logger.debug('Follow: %s started following %s', follower, following)
        await self.send_notification(trx_id=op['trx_id'],
                                     from_username=follower,
                                     to_username=following,
                                     json_data=json.dumps(follow_data[1]),
                                     type=FOLLOW,
                                     priority_level=PRIORITY_LEVELS['low'])
        return True

    async def handle_account_update(self, op):
        logger.debug('handle_account_update recevied %s op' % op['op'][0])
        return True

    async def handle_send(self, op):
        op_data = op['op'][1]
        send_data = {
            'amount': op_data['amount'],
            'from': op_data['from'],
            'memo': op_data['memo'],
            'to': op_data['to'],
        }
        logger.debug('Send: %s sent %s to %s',
            send_data['from'], send_data['amount'], send_data['to'])
        await self.send_notification(trx_id=op['trx_id'],
                                     to_username=send_data['from'],
                                     json_data=json.dumps(send_data),
                                     type=SEND_STEEM,
                                     priority_level=PRIORITY_LEVELS['low'])
        return True

    async def handle_receive(self, op):
        op_data = op['op'][1]
        receive_data = {
            'amount': op_data['amount'],
            'from': op_data['from'],
            'memo': op_data['memo'],
            'to': op_data['to'],
        }
        logger.debug('Receive: %s got %s from %s',
            receive_data['to'], receive_data['amount'], receive_data['from'])
        await self.send_notification(trx_id=op['trx_id'],
                                     to_username=receive_data['to'],
                                     from_username=receive_data['from'],
                                     json_data=json.dumps(receive_data),
                                     type=RECEIVE_STEEM,
                                     priority_level=PRIORITY_LEVELS['low'])
        return True

    async def handle_power_down(self, op):
        logger.debug('handle_power_down recevied %s op' % ['op'][0])
        return True

    async def handle_mention(self, op):
        comment_data = op['op'][1]
        haystack = comment_data['body'] + '\n'
        data = {
            'author': comment_data['author'],
            'permlink': comment_data['permlink'],
        }
        for match in re.findall(MENTION_PATTERN, haystack):
            # TODO: only allow N mentions per operation?
            # TODO: validate mentioned user exists on chain?
            logger.debug('Mention: %s mentioned %s', data['author'], match)
            await self.send_notification(trx_id=op['trx_id'],
                                         to_username=match,
                                         from_username=data['author'],
                                         json_data=json.dumps(data),
                                         type=MENTION,
                                         priority_level=PRIORITY_LEVELS['low'])
        return True

    async def handle_comment_reply(self, op):
        logger.debug('handle_comment_reply recevied %s op' % ['op'][0])
        return True

    async def handle_post_reply(self, op):
        logger.debug('handle_post_reply recevied %s op' % ['op'][0])
        return True

    async def handle_resteem(self, op):
        op_data = op['op'][1]
        resteem_data = json.loads(op_data['json'])
        if resteem_data[0] != 'reblog':
            return True
        account = resteem_data[1]['account']
        author = resteem_data[1]['author']
        permlink = resteem_data[1]['permlink']
        if len(op_data['required_posting_auths']) != 1:
            logger.error('inavlid resteem op, got %d posting auths, expected 1' % op_data['required_posting_auths'])
            return True
        if op_data['required_posting_auths'][0] != account:
            logger.error('invalid resteem op, account must be signer')
            return True
        logger.debug('Resteem: %s reblogged @%s/%s' % (account, author, permlink))
        await self.send_notification(trx_id=op['trx_id'],
                                     from_username=account,
                                     to_username=author,
                                     json_data=json.dumps(resteem_data[1]),
                                     type=RESTEEM,
                                     priority_level=PRIORITY_LEVELS['low'])
        return True

    async def notify(self, blockchain_op):
        """ Handle notification for a particular op
        """
        logger.debug('Got operation from blockchain: %s', str(blockchain_op))
        # vote
        if blockchain_op['op'][0] == 'vote':
            return await self.handle_vote(blockchain_op)
            # handle notifications for upvotes here based on user preferences in DB

        # follow, resteem
        elif blockchain_op['op'][0] == 'custom_json':
            if blockchain_op['op'][1]['id'] == 'follow':
                logger.debug('Incoming custom_json operation')
                # handle follow notifications here
                return await asyncio.gather(
                    self.handle_follow(blockchain_op),
                    self.handle_resteem(blockchain_op))

        # account_update
        elif blockchain_op['op'][0] == 'account_update':
            logger.debug('Incoming account_update operation')
            return await self.handle_account_update(blockchain_op)

        # send, receive
        elif blockchain_op['op'][0] == 'transfer':
            logger.debug('Incoming transfer operation')
            return await asyncio.gather(
                self.handle_send(blockchain_op),
                self.handle_receive(blockchain_op))

        # power_down
        elif blockchain_op['op'][0] == 'withdraw_vesting':
            logger.debug('Incoming withdraw_vesting operation')
            return await self.handle_power_down(blockchain_op)

        # mention, comment-reply, post-reply
        elif blockchain_op['op'][0] == 'comment':
            logger.debug('Incoming comment operation')
            return await asyncio.gather(
                   self.handle_mention(blockchain_op),
                   self.handle_comment_reply(blockchain_op) ,
                   self.handle_post_reply(blockchain_op))

        # reward
        # feed
        return True  # return this or the op will be requeued

    async def run_queue(self, q):
        while not q.empty():
            op = await q.get()

            resp = await self.notify(op)
            if not resp:
                logger.debug('Re-queueing operation: %s' % str(op))
                return op
        return None

    async def async_ops(self, loop, b):
        ops = b.stream_from(start_block=int(
                self.yo_app.config.config_data['blockchain_follower'][
                    'start_block']))
        while True:
            yield await loop.run_in_executor(None, next, ops)

    async def async_task(self, yo_app):
        queue = asyncio.Queue()
        logger.info('Blockchain follower started')
        while True:
            try:
                b = Blockchain()
                while True:
                    try:
                        async for op in self.async_ops(yo_app.loop, b):
                            await queue.put(op)
                            await asyncio.sleep(0)
                            runner_resp = await self.run_queue(queue)
                            if not (runner_resp is None): queue.put(runner_resp)
                    except Exception as e:
                        logger.exception('Exception occurred')
            except Exception as e:
                logger.exception('Exception occurred')

