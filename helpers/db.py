import asyncio
from contextlib import asynccontextmanager

import aiomysql
import ujson
from pymysql.err import OperationalError

from helpers.config import mysql_server, mysql_password, mysql_user


class _BotDB:
    pool: aiomysql.Pool = None
    loop = asyncio.get_event_loop()

    async def connect(self):
        self.pool = await aiomysql.create_pool(
            host=mysql_server, user=mysql_user, password=mysql_password, db='bot_db', autocommit=True, loop=self.loop)

    @asynccontextmanager
    async def cursor(self):
        if self.pool is None:
            await self.connect()

        conn_cm = self.pool.acquire()
        conn = await conn_cm.__aenter__()

        cur_cm = conn.cursor()
        try:
            yield await cur_cm.__aenter__()

        finally:
            await conn_cm.__aexit__(None, None, None)
            await cur_cm.__aexit__(None, None, None)

    async def execute(self, query, args=None, fetch=0, trycount=5):
        print(query, args)
        try:
            async with self.cursor() as cur:
                cur: aiomysql.Cursor
                await cur.execute(query, args)

                if fetch == 1:
                    return await cur.fetchone()
                if fetch == 2:
                    return await cur.fetchall()
                if fetch == 3:
                    return cur.lastrowid
        except OperationalError:
            if trycount > 0:
                return await self.execute(query, args, fetch, trycount - 1)

    async def fetchone(self, query, args=None):
        return await self.execute(query, args, 1)

    async def fetchall(self, query, args=None):
        return await self.execute(query, args, 2)

    async def autoincrement(self, query, args=None):
        return await self.execute(query, args, 3)

    async def set_state(self, chat_id, state: int, state_data: str = None):
        await self.execute("UPDATE users SET state = %s, state_data = %s WHERE id = %s;",
                           (state, state_data, chat_id))

    async def get_state(self, chat_id):
        state, state_data = await self.fetchone("SELECT state, state_data FROM users WHERE id = %s", chat_id)

        return state, state_data


BotDB = _BotDB()
