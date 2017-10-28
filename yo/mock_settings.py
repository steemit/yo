# coding=utf-8
""" Maintains in-memory mock per-user settings
"""

NOTIFY_TYPES = ('power_down', 'power_up', 'resteem', 'feed', 'reward', 'send',
                'mention', 'follow', 'vote', 'comment_reply', 'post_reply',
                'account_update', 'message', 'receive')


class YoMockSettings:
    """ A set of in-memory mock notifications
   """

    def __init__(self):
        self.transports_by_user = {}
        self.reset()

    def reset(self):
        """ Reset the current status of the mock settings
           This does NOT create new data, default settings are created for users first time get_transports() is called on them

           TODO: take care of the case where the user does not exist on the blockchain and don't create default settings
       """

    def create_defaults(self):
        """ Creates sane defaults
           
           Since this is for the mock API, the email transport is test@example.com, obviously this should be changed to end user address ;)
           The returned defaults will send all notification types to email and to "wwwpoll", wwwpoll being the DB table polled by the API for use in condenser
       """

        return {
            'email':   {
                'notification_types': NOTIFY_TYPES,
                'sub_data':           'test@example.com'
            },
            'wwwpoll': {
                'notification_types': NOTIFY_TYPES,
                'sub_data':           {}
            }
        }

    def get_transports(self, username):
        """ Get configured transports for the specified user, creating default ones if none exist
       """
        if not username in self.transports_by_user.keys():
            self.transports_by_user[username] = self.create_defaults()
        return self.transports_by_user[username]

    def set_transports(self, username, transports):
        """ Set transports for the specified user ;)

       Does no sanity checking on the transports object, that's the API server's job
       """
        self.transports_by_user[username] = transports
        return transports
