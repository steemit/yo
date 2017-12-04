# -*- coding: utf-8 -*-
import abc
import asyncio
from concurrent.futures import CancelledError
from functools import partial
from typing import Callable

import aiojobs
import structlog

from .registration import Registration
from .registration import ServiceState

logger = structlog.getLogger(__name__)


class YoAbstractServiceClass(abc.ABC):
    @abc.abstractmethod
    def get_name(self) -> str:
        pass

    @abc.abstractmethod
    def init_api(self) -> None:
        pass

    @property
    @abc.abstractmethod
    def loop(self) -> asyncio.AbstractEventLoop:
        pass

    @abc.abstractmethod
    async def execute_sync(self,
                           func: Callable,
                           *args,
                           db_func: bool = False,
                           **kwargs):
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
    def register(self) -> None:
        pass

    @abc.abstractmethod
    def unregister(self) -> None:
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
    def enable_heartbeat(self) -> None:
        pass

    @abc.abstractmethod
    def disable_heartbeat(self) -> None:
        pass

    @abc.abstractmethod
    def shutdown(self) -> None:
        pass

    @abc.abstractmethod
    async def main_task(self) -> None:
        pass


# pylint: disable=too-many-instance-attributes
class YoBaseService(YoAbstractServiceClass):
    service_name = 'base'
    private_api_methods = {}

    def __init__(self, yo_app=None, config=None, db=None):
        self.yo_app = yo_app
        self.config = config or getattr(yo_app, 'config', {})
        self.db = db or getattr(yo_app, 'db', None)

        self.service_status = ServiceState.DISABLED
        self.service_id = None
        self.service_extra = dict()

        self.scheduler = None
        self.heartbeat_status = ServiceState.ENABLED

        self.heartbeat_interval = 10
        self.service_interval = 1

        self.log = logger.bind(service_name=self.service_name)

    def get_name(self):
        return self.service_name

    def init_api(self):
        self.log.info('initializing')
        self.log.info('creating job scheudler')
        self.scheduler = self.loop.run_until_complete(
            aiojobs.create_scheduler(
                close_timeout=self.heartbeat_interval + 2))
        self.log.info('registering')
        self.register()

        self.log.info('starting heartbeat task')
        asyncio.ensure_future(self.scheduler.spawn(self.heartbeat()))

    @property
    def loop(self):
        return self.yo_app.loop

    async def execute_sync(self, func, *args, db_func=False, **kwargs):
        try:
            if db_func and self.db.backend == 'sqlite':
                return func(*args, **kwargs)
            part_func = partial(func, *args, **kwargs)
            return await self.loop.run_in_executor(None, part_func)
        except CancelledError:
            self.log.debug('ignoring CancelledError')

    async def heartbeat(self):
        self.log.info('heartbeat task executing')
        try:
            self.log.info('heartbeat sending info')
            new_registration = await self.execute_sync(
                self.db.heartbeat, self.registration, db_func=True)
            self.update(new_registration)

        except Exception:
            self.log.exception('heartbeat task error')
        finally:
            if self.heartbeat_status:
                await asyncio.sleep(self.heartbeat_interval)
                await self.scheduler.spawn(self.heartbeat())
            else:
                self.log.info('heartbeat task exiting')

    @property
    def registration(self):
        return Registration(
            service_name=self.service_name,
            service_id=self.service_id,
            service_status=self.service_status,
            service_extra=self.service_extra)

    def update(self, registration):
        self.log.debug('update requested')
        self.service_id = registration.service_id
        self.handle_service_extra(registration.service_extra)
        self.log = self.log.bind(**registration.asdict())
        if self.service_status != registration.service_status:
            self.log.info('updating')
            self.toggle_service_status()
            self.log.debug(str(self.registration))
        else:
            self.log.debug('update noop')

    def register(self):
        self.log.info('attempting to register')
        registration = self.db.register_service(service_name=self.service_name)
        self.log.info('registered')
        self.update(registration)

    def unregister(self):
        self.log.info('attempting to unregister')
        self.db.unregister_service(self.registration)
        self.log.info('unregistered')

    def handle_service_extra(self, extra):
        pass

    async def service_task(self):
        self.log.info('main task executing')
        try:
            self.log.debug('main task executed')
            await self.main_task()
        except Exception:
            self.log.exception('main task error', exc_info=True)
        finally:
            if self.service_status:
                await asyncio.sleep(self.heartbeat_interval)
                await self.scheduler.spawn(self.service_task())
            else:
                self.log.info('main task exiting')

    def enable_service(self):
        self.log.info('enabling main task')
        self.service_status = ServiceState.ENABLED
        asyncio.ensure_future(self.scheduler.spawn(self.service_task()))

    def disable_service(self):
        self.log.info('disabling main task')
        self.service_status = ServiceState.DISABLED

    def toggle_service_status(self):
        self.log.info('toggling main task')
        if self.service_status:
            self.disable_service()
        else:
            self.enable_service()

    def enable_heartbeat(self):
        self.log.info('enabling heartbeat task')
        self.heartbeat_status = ServiceState.ENABLED

    def disable_heartbeat(self):
        self.log.info('disabling heartbeat task')
        self.heartbeat_status = ServiceState.DISABLED

    async def shutdown(self):
        self.log.info('shutting down')
        try:
            self.disable_heartbeat()
        except BaseException:
            self.log.exception('error disabling heartbeat')

        try:
            if self.service_status:
                self.disable_service()
        except BaseException:
            self.log.exception('error disabling service')

        try:
            logger.info('unregistering')
            self.unregister()
        except BaseException:
            self.log.exception('error unregistering service')

        self.log.info('terminating scheduler')
        try:
            await self.scheduler.close()
        except BaseException:
            self.log.exception('error closing scheduler')

    async def main_task(self):
        pass
