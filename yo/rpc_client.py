# coding=utf-8
import asyncio

import aiohttp
import structlog

from yo.json import loads
from yo.json import dumps

logger = structlog.getLogger(__name__, source='rpc_client')

from rpcauth import sign

async def auth_request(jsonrpc_request:dict, account:str='test', keys:tuple=('test'), url:str='https://api.steemit.com') -> dict:
    signed_request = sign(jsonrpc_request, account, list(keys))
    async with aiohttp.ClientSession(json_serialize=dumps) as session:
        async with session.post(url, json=signed_request, encoding='utf8') as resp:
            return await resp.json(encoding='utf8', loads=loads)

async def get_user_data(username:str, account:str=None, keys:tuple=None, url:str='https://api.steemit.com') -> dict:
    rpc_request = {
        'id':     1, 'jsonrpc': '2.0',
        'method': 'conveyor.get_user_data',
        'params': {'username': username}
    }
    response = await auth_request(rpc_request, account=account, keys=keys, url=url)
    return response['result']
