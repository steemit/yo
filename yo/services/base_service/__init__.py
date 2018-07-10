# -*- coding: utf-8 -*-
import abc
import asyncio
from concurrent.futures import CancelledError
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from typing import Callable
import time

import aiojobs
import asyncpg
import structlog
import uvloop


from .registration import Registration
from .registration import ServiceState



asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logger = structlog.getLogger(__name__)

service_config = {
    'heartbeat_enabled': True,
    'heartbeat_interval': 10,
    'service_interval': 1,
    'service_enabled': True,
    'service_name': None,
    'service_id': None,
    'service_extra': {}
}


class YoAbstractServiceClass(abc.ABC):
    @abc.abstractmethod
    def get_name(self) -> str:
        pass

    @abc.abstractmethod
    def run(self) -> None:
        pass

    @property
    @abc.abstractmethod
    def loop(self) -> asyncio.AbstractEventLoop:
        pass

    @abc.abstractmethod
    async def execute_sync(self, func: Callable, *args, db_func: bool = False, **kwargs):
        pass

    @abc.abstractmethod
    async def heartbeat(self) -> None:
        pass

    @property
    @abc.abstractmethod
    def registration(self) -> Registration:
        pass

    @abc.abstractmethod
    def update(self, registration: Registration) -> None:
        pass

    @abc.abstractmethod
    def deregister(self) -> None:
        pass

    @abc.abstractmethod
    def handle_service_extra(self, extra: dict) -> None:
        pass

    @abc.abstractmethod
    async def service_task(self) -> None:
        pass

    @abc.abstractmethod
    def enable_service(self) -> None:
        pass

    @abc.abstractmethod
    def disable_service(self) -> None:
        pass

    @abc.abstractmethod
    def toggle_service_status(self) -> None:
        pass



    @abc.abstractmethod
    def shutdown(self) -> None:
        pass





'''
Service States
--------------
disabled: heartbeat task is running, service task is not
enabled: heatbeat task and service task are running
'''

# pylint: disable=too-many-instance-attributes
class YoBaseService(YoAbstractServiceClass):
    service_name = 'base'
    private_api_methods = {}

    def __init__(self, database_url=None, loop=None):
        self.db_url = database_url
        self._loop = loop or asyncio.get_event_loop()
        self.db_pool = self.loop.run_until_complete(
            asyncpg.create_pool(self.db_url, loop=loop))
        self.async_db_engine = self.db_pool

        self.service_status = ServiceState.DISABLED
        self.service_id = None
        self.service_extra = dict()

        self.heartbeat_interval = 10
        self._heatbeat_task = None
        self._service_task = None

        self.log = logger.bind(service_name=self.service_name)

    def get_name(self):
        return self.service_name

    def run(self):
        self.log.info('initializing')
        try:
            self.loop.run_until_complete(self.heartbeat())
        finally:
            self.loop.run_until_complete(self.shutdown())
            self.loop.close()

    @property
    def loop(self):
        return self._loop

    async def execute_sync(self, func, *args, **kwargs):
        try:
            part_func = partial(func, *args, **kwargs)
            return await self.loop.run_in_executor(None, part_func)
        except CancelledError:
            self.log.debug('ignoring CancelledError')




    async def heartbeat(self):
        self.log.info('heartbeat task executing')
        from ...db.services import heartbeat
        async with self.async_db_engine.acquire() as conn:
            while True:
                try:
                    self.log.debug('heartbeating')
                    new_registration = await heartbeat(conn,
                                                           self.registration)
                    self.update(new_registration)
                    self.log.debug('heatbeat sleeping', interval=self.heartbeat_interval)
                    if self.service_status is ServiceState.ENABLED and self._service_task is None:
                        task = self.loop
                    await asyncio.sleep(self.heartbeat_interval)
                except Exception:
                    self.log.error('heartbeat task error', exc_info=True)
                    break
        self.log.info('heartbeat task exiting')

    @property
    def registration(self):
        return Registration(
            service_name=self.service_name,
            service_id=self.service_id,
            service_status=self.service_status,
            service_extra=self.service_extra)

    def update(self, registration):
        self.log.debug(
            'update requested',
            registration=registration,
            current=self.registration)
        self.service_id = registration.service_id
        self.handle_service_extra(registration.service_extra)
        self.log = self.log.bind(**registration.asdict())

        if self.service_status != registration.service_status:
            self.log.info('service status changed',
                          new_status=registration.service_status)
            self.toggle_service_status()

    async def deregister(self):
        from ...db.services import unregister_service
        self.log.info('attempting to deregister')
        async with self.async_db_engine.acquire() as conn:
            await unregister_service(conn, self.registration)
        self.log.info('deregister success')

    def handle_service_extra(self, extra):
        pass

    async def service_task(self):
        self.log.info('main task executing')
        try:
            await self.loop.run_in_executor(ProcessPoolExecutor(), self.main_task)
        except asyncio.CancelledError:
            self.log.info('service task cancelled')
            raise
        except Exception as e:
            self.log.exception('main task error', exc_info=e)
            raise e
        finally:
            self._service_task = None

    def enable_service(self):
        self.log.info('enabling main task')
        self.service_status = ServiceState.ENABLED
        self._service_task = asyncio.ensure_future(self.service_task())


    def disable_service(self):
        self.log.info('disabling main task')
        self.service_status = ServiceState.DISABLED
        self._service_task.cancel()
        self._service_task = None

    def toggle_service_status(self):
        self.log.info('toggling main task')
        if self.service_status:
            self.disable_service()
        else:
            self.enable_service()

    async def shutdown(self):
        self.log.info('shutting down')
        try:
            logger.info('unregistering')
            await self.deregister()
        except BaseException as e:
            self.log.exception('error unregistering service',e=e)
        try:
            if self.service_status:
                self.disable_service()
        except BaseException as e:
            self.log.exception('error disabling service',e=e)

        self.db_pool.terminate()
        self.loop.stop()
