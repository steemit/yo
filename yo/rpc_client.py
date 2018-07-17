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

