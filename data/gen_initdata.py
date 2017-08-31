import json

data = (('user_transports_table',{'username'      :'garethnelsonuk',
                                  'notify_type'   :'vote',
                                  'transport_type':'email',
                                  'sub_data'      :'gareth@steemit.com'}))

print json.dumps(data)
