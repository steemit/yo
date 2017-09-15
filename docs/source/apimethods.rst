Yo API
======

This page describes the external API accessible from other programs via JSON-RPC over HTTP.

Notification priority levels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The notifications sent by Yo are rate limited according to the priority level they belong to. For each priority level we have a hard limit which can never be bypassed and a soft limit which
can optionally be bypassed. The rate limiter considers all notifications of the priority level and all higher levels, so for example when processing a LOW priority all notifications
at ALWAYS,PRIORITY,NORMAL and LOW will be taken into account, while for ALWAYS only ALWAYS will be taken into account.

============== ========== ==========
priority level hard limit soft limit
============== ========== ==========
ALWAYS         10/hour    10/hour
PRIORITY       10/hour    1/hour
NORMAL         3/minute   1/minute
LOW            10/hour    1/hour
MARKETING      1/hour     1/day
============== ========== ==========

Supported notification types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Notifications are represented as the actual operation pulled from the blockchain in a dictionary and each notification also has a default priority level:

================= ======== =========
notification type priority fields
================= ======== =========
feed              low      
reward            normal   
send              priority from
\                 \        to
\                 \        amount
\                 \        memo
mention           normal   
follow            low      
vote              low      voter
\                 \        author
\                 \        permlink
\                 \        weight
comment_reply     normal
post_reply        normal
account_update    priority
receive           normal   from
\                 \        to
\                 \        amount
\                 \        memo
================= ======== =========

Note that not all are currently implemented at this point

Supported transports
~~~~~~~~~~~~~~~~~~~~
Notifications may be sent over various transports depending on configuration. Each transport will send notification data to the end user via a specified "subscription" stored in the database
as sub_data. Please reference the field below for syntax and format of the sub_data field:

=========== ==================== ================
transport   sub_data description example sub_data
=========== ==================== ================
email       email address        test@example.com 
wwwpush     VAPID subscription   {
\           \                     endpoint: "https://android.googleapis.com/gcm/send/a-subscription-id",
\           \                     keys: {
\           \                       auth: 'AEl35...7fG',
\           \                       p256dh: 'Fg5t8...2rC'
\           \                     }
\           \                    }
=========== ==================== ================



Supported API methods
~~~~~~~~~~~~~~~~~~~~~

Please note that not all these functions will be implemented yet.

.. py:function:: yo.get_vapid_key()

   Retrieve the public VAPID key for use in creating a subscription

   :return: The base64-encoded public VAPID key
   :rtype: str

.. py:function:: yo.enable_transports(username=None, transports={})

   Update/enable transports for particular notification types

   :param str username:    The user to set transports for
   :param dict transports: A dictionary mapping notification types to lists of transports to use
   :return:                A dictionary with status field set to OK if successful
   :rtype: dict
