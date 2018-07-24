# coding=utf-8

from tests.conftest import create_mocked_pool
import yo.db
import asyncpg
import asynctest
import pytest

@pytest.mark.async
async def test_mocked_pool(mocked_pool):
    mocked_create_pool = asynctest.Mock(return_value=mocked_pool)
    with asynctest.patch('asyncpg.pool.create_pool', new=mocked_create_pool):
        pool = asyncpg.pool.create_pool('nonsense://dsn')
        asyncpg.pool.create_pool.assert_called_once()
        assert pool is mocked_pool
        await pool.fetchval()
        pool.fetchval.assert_called_once()
        await pool.fetchrow()
        pool.fetchrow.assert_called_once()
        await pool.fetch()
        pool.fetch.assert_called_once()
        await pool.execute()
        pool.execute.assert_called_once()
        async with pool.acquire() as conn:
            pool.acquire.assert_called_once()
            await conn.fetchval()
            conn.fetchval.assert_called_once()
            await conn.fetchrow()
            conn.fetchrow.assert_called_once()
            await conn.fetch()
            conn.fetch.assert_called_once()
            await conn.execute()
            conn.execute.assert_called_once()
            async with conn.transaction():
                conn.transaction.assert_called_once()
                await conn.fetchval()
                assert conn.fetchval.call_count == 2
                await conn.fetchrow()
                assert conn.fetchrow.call_count == 2
                await conn.fetch()
                assert conn.fetch.call_count == 2
                await conn.execute()
                assert conn.execute.call_count == 2
            tr = conn.transaction()
            assert conn.transaction.call_count == 2
            await tr.start()
            tr.start.assert_called_once()
            await tr.rollback()
            tr.rollback.assert_called_once()
            await tr.commit()
            tr.commit.assert_called_once()

@pytest.mark.async
async def test_mocked_create_asyncpg_pool(mocked_pool):
    with asynctest.patch('yo.db.create_asyncpg_pool', new=mocked_pool):
        pool = await yo.db.create_asyncpg_pool('nonsense://dsn')
        yo.db.create_asyncpg_pool.assert_called_once()
        assert pool is mocked_pool
        await pool.fetchval()
        pool.fetchval.assert_called_once()
        await pool.fetchrow()
        pool.fetchrow.assert_called_once()
        await pool.fetch()
        pool.fetch.assert_called_once()
        await pool.execute()
        pool.execute.assert_called_once()
        async with pool.acquire() as conn:
            pool.acquire.assert_called_once()
            await conn.fetchval()
            conn.fetchval.assert_called_once()
            await conn.fetchrow()
            conn.fetchrow.assert_called_once()
            await conn.fetch()
            conn.fetch.assert_called_once()
            await conn.execute()
            conn.execute.assert_called_once()
            async with conn.transaction():
                conn.transaction.assert_called_once()
                await conn.fetchval()
                assert conn.fetchval.call_count == 2
                await conn.fetchrow()
                assert conn.fetchrow.call_count == 2
                await conn.fetch()
                assert conn.fetch.call_count == 2
                await conn.execute()
                assert conn.execute.call_count == 2
            tr = conn.transaction()
            assert conn.transaction.call_count == 2
            await tr.start()
            tr.start.assert_called_once()
            await tr.rollback()
            tr.rollback.assert_called_once()
            await tr.commit()
            tr.commit.assert_called_once()

@pytest.mark.async
async def test_mocked_create_asyncpg_conn(mocked_conn):
    with asynctest.patch('yo.db.create_asyncpg_conn', new=mocked_conn):
        conn = await yo.db.create_asyncpg_conn('nonsense://dsn')
        assert conn is mocked_conn
        yo.db.create_asyncpg_conn.assert_called_once()
        await conn.fetchval()
        conn.fetchval.assert_called_once()
        await conn.fetchrow()
        conn.fetchrow.assert_called_once()
        await conn.fetch()
        conn.fetch.assert_called_once()
        await conn.execute()
        conn.execute.assert_called_once()
        async with conn.transaction():
            conn.transaction.assert_called_once()
            await conn.fetchval()
            assert conn.fetchval.call_count == 2
            await conn.fetchrow()
            assert conn.fetchrow.call_count == 2
            await conn.fetch()
            assert conn.fetch.call_count == 2
            await conn.execute()
            assert conn.execute.call_count == 2
        tr = conn.transaction()
        assert conn.transaction.call_count == 2
        await tr.start()
        tr.start.assert_called_once()
        await tr.rollback()
        tr.rollback.assert_called_once()
        await tr.commit()
        tr.commit.assert_called_once()
