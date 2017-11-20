# Example notifications

This file contains some example notifications - one for each notification type as returned by the wwwpoll API interface immediately after creation.

## account_update
```js  
        {  
            "notify_id": "be31a66e-bb6f-11e7-90d4-901b0e968c44",
            "notify_type": "account_update",
            "created": "2017-10-27T01:31:29.382749",
            "updated": "2017-10-27T15:16:06.178975",
            "read": false,
            "shown": false,
            "username": "test_user",
            "data": {
                "account_metadata": {
                     "profile": {
                        "profile_image": "https://www.example.com/test.png",
                        "name": "Test User"
                     }
                }

            }
        }
```

## comment_reply


```js  
        {  
            "notify_id": "f4648680-bb73-11e7-8683-901b0e968c44",
            "notify_type": "comment_reply",
            "created": "2017-10-28T00:10:29.523562",
            "updated": "2017-10-28T00:11:29.125634",
            "read": false,
            "shown": false,
            "username": "test_user",
            "data": {
                "account_metadata": {
                     "profile": {
                        "profile_image": "https://www.example.com/test.png",
                        "name": "Test User"
                     }
                }

            }
        }
```

## savings_withdraw
## feed
## follow
## mention
## post_reply
## power_down
## send
## receive
## resteem
## reward
## vote
