# -*- coding: utf-8 -*-
import sqlalchemy as sa
import structlog


from ..schema import NotificationType
from ..schema import TransportType
from ..schema import Priority

from .users import get_user_transports_for_notification


logger = structlog.getLogger(__name__, source='YoDB')

from yo.db import metadata
from .queue import put_many

class DuplicateNotificationError(BaseException):
    pass

notifications_table = sa.Table(
    'notifications',
    metadata,
    sa.Column('nid', sa.BigInteger(), primary_key=True),
    sa.Column('eid', sa.Text()),
    sa.Column('notify_type', sa.Integer(), nullable=False),
    sa.Column('to_username',sa.Text(),nullable=False),
    sa.Column('from_username',sa.Text(),nullable=True),
    sa.Column('json_data', sa.UnicodeText()),
    sa.Column('created', sa.DateTime, default=sa.func.now(), nullable=False),
    sa.Column('priority', sa.Integer, default=Priority.normal.value),
    sa.Index('ix_notifications_unique','eid','to_username',unique=True)
)

INSERT_NOTIFICATON_STMT = '''
INSERT INTO notifications(eid, notify_type, to_username, from_username, json_data, priority, created)
VALUES($1, $2, $3, $4, $5, $6, NOW()) 
ON CONFLICT DO NOTHING
RETURNING nid'''



GET_LAST_BLOCK_STMT = '''
SELECT eid FROM notifications ORDER BY DESC nid LIMIT 1; 
'''


'''
flow
bf detects operation
op's handlers are run tp generate event

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


# create notification methods
async def create_notification(pool,
                              eid:str = None,
                              notify_type:NotificationType = None,
                              to_username:str = None,
                              from_username:str = None,
                              json_data:dict = None,
                              priority: Priority = None):
    logger.debug('create_notification',
                 eid=eid,
                 notify_type=notify_type,
                 to_username=to_username,
                 from_username=from_username,
                 json_data=json_data,
                 priority=priority)
    async with pool.acquire() as conn:
        try:
            async with conn.transaction():
                # store notification
                nid = await conn.fetchval(INSERT_NOTIFICATON_STMT, eid, notify_type, to_username, from_username, json_data, priority)
                if not nid:
                    raise DuplicateNotificationError()

                # load applicable user transport settings
                enabled_transports = await get_user_transports_for_notification(conn, to_username, notify_type)
                logger.debug('enabled_transports',acct=to_username,enabled=enabled_transports)
                if not enabled_transports:
                    return True

                # create/put transport-notifications
                queue_item = {
                    'nid':           nid,
                    'eid':           eid,
                    'notify_type':   notify_type.value,
                    'to_username':   to_username,
                    'from_username': from_username,
                    'json_data':     json_data,
                    'priority':      priority
                }
                queue_items = [(queue_item, TransportType[tt]) for tt in enabled_transports]
                await put_many(conn, queue_items)

                logger.debug('notifications created', notify_type=notify_type.name, transports=enabled_transports)
                return True

        except DuplicateNotificationError:
            logger.debug('duplicate notification', eid=eid,
                         to_username=to_username)
            return True

        except Exception as e:
            logger.exception('error creating notification')
            return False


async def get_last_processed_block(conn):
    eid = await conn.fetchval(GET_LAST_BLOCK_STMT)
    if eid:
        return int(eid.split('/')[0]) - 1
    return 1
