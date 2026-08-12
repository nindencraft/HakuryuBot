import asyncpg
import os

async def get_db():
    DATABASE_URL = os.getenv("DATABASE_URL")   # lê sempre que a função é chamada
    return await asyncpg.connect(
        DATABASE_URL,
        statement_cache_size=0,
        ssl='require'
    )


async def fetch_one(query, *args):
    conn = await get_db()
    try:
        return await conn.fetchrow(query, *args)
    finally:
        await conn.close()

async def fetch_all(query, *args):
    conn = await get_db()
    try:
        return await conn.fetch(query, *args)
    finally:
        await conn.close()

async def execute(query, *args):
    conn = await get_db()
    try:
        return await conn.execute(query, *args)
    finally:
        await conn.close()