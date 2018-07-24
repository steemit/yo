# -*- coding: utf-8 -*-

import sqlalchemy as sa
import structlog

from ..services.base_service.registration import Registration
from ..services.base_service.registration import ServiceState

from yo.db import metadata

logger = structlog.getLogger(__name__, source='yo.db.services')

CREATE_SERVICE_STMT = '''INSERT INTO services(name,extra,updated) VALUES($1,$2,NOW()) RETURNING sid'''
DELETE_SERVICE_STMT = '''DELETE FROM services WHERE sid = $1'''
GET_SERVICE_STMT = '''SELECT * FROM services WHERE sid = $1'''
UPDATE_SERVICE_STATUS_STMT = '''UPDATE services SET status = $1, updated = NOW() WHERE sid = $2'''
UPDATE_SERVICE_TIMESTAMP_STMT = '''UPDATE services SET updated = NOW() WHERE sid = $1'''

SELECT_FOR_UPDATE_STMT = '''SELECT * FROM services WHERE name = $1 FOR UPDATE'''

PRUNE_STALE_SERVICES_STMT = '''DELETE FROM services WHERE updated < NOW() - interval '25 seconds' '''
DISABLE_ALL_SERVICES_STMT = '''UPDATE services SET status = $1, updated=NOW() WHERE name = $2'''

services_table = sa.Table('services', metadata,
                          sa.Column('sid', sa.Integer, primary_key=True),
                          sa.Column('name', sa.Text, nullable=False),
                          sa.Column(
                              'status',
                              sa.Integer,
                              default=int(ServiceState.DISABLED),
                              nullable=False),
                          sa.Column('extra', sa.Text),
                          sa.Column(
                              'updated',
                              sa.DateTime,
                              nullable=False,
                              default=sa.func.now(),
                              onupdate=sa.func.now()),
                          sa.Index(
                              'only_one_enabled_service',
                              'name',
                              'status',
                              unique=True,
                              postgresql_where='yo_services.status' == 1))



# service methods
# pylint: disable=no-self-use
async def register_service(conn, service_name, service_extra=None):
    logger.info('registering service', service_name=service_name)

    # add service to services table
    async with conn.transaction():
        service_id = await conn.fetchval(CREATE_SERVICE_STMT, service_name, service_extra)

    result = Registration(
        service_name=service_name,
        service_id=service_id,
        service_status=ServiceState.DISABLED,
        service_extra={})
    logger.info('service registered', registration=result)
    return result
# pylint: enable=no-self-use

async def unregister_service(conn, registration):
    logger.info('unregistering service', registration=registration)

    async with conn.transaction():
        # remove service from services table
        await conn.execute(DELETE_SERVICE_STMT,
                               registration.service_id)
    logger.debug(
        'service unregistered',
        service_name=registration.service_name,
        service_id=registration.service_id)


async def get_service(conn, service_id):
    row = await conn.fetchrow(GET_SERVICE_STMT, service_id)
    return Registration(
        service_name=row['name'],
        service_id=row['sid'],
        service_status=row['status'],
        service_extra=row['extra'])

# pylint: disable=too-many-locals
async def heartbeat(conn, registration: Registration) -> Registration:
    service_name = registration.service_name
    service_id = registration.service_id
    log = logger.bind(service_id=service_id, service_name=service_name)
    log.info('heartbeat received')

    # prune stale services

    await prune_stale_services(conn)

    # lock services of same type
    async with conn.transaction():

        services = await conn.fetch(SELECT_FOR_UPDATE_STMT,registration.service_name)
        existing_service_ids = set(s['sid'] for s in services)

        # service not stored in table
        if not service_id or service_id not in existing_service_ids:
            # assign id
            registration = await register_service(conn, registration.service_name)
            service_name = registration.service_name
            service_id = registration.service_id
            log = logger.bind(service_id=service_id, service_name=service_name)

        # adjust enabled services
        enabled_services_count = sum(s['status'] for s in services)
        log.debug('enabled services count', count=enabled_services_count)

        # enable service if it is the only one registered
        if enabled_services_count != 1:
            log.info('enabled services count != 1', count=enabled_services_count)
            await disable_services(conn, service_name)
            log.info('enabling service')
            await enable_service(conn, service_id)
        else:
            log.debug('updating heartbeat datetime')
            await update_service(conn, service_id)

    # read state from new transaction and return it to service

    # read service status from db and return it to service
    registration = await get_service(conn, service_id)
    log.debug('registration result', registration=registration)
    return registration

# pylint: disable=no-self-use
async def enable_service(conn, service_id):
    await conn.execute(UPDATE_SERVICE_STATUS_STMT,
                                int(ServiceState.ENABLED),
                                service_id)
    logger.debug('enable service')


async def update_service(conn, service_id):
    return await conn.execute(UPDATE_SERVICE_TIMESTAMP_STMT,
                                int(service_id))


async def disable_services(conn, service_name):
    logger.info('disabling all instances of service type', type=service_name)
    await conn.execute(DISABLE_ALL_SERVICES_STMT,
                                int(ServiceState.DISABLED),
                                service_name)
    logger.debug('disable all services')

async def prune_stale_services(conn):
    logger.debug('pruning stale services')
    await conn.execute(PRUNE_STALE_SERVICES_STMT)
    logger.debug('pruned stale services')

