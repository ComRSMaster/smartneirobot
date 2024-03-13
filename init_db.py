import asyncio
import sys

import aiomysql


async def migrate():
    _, host, user, password = sys.argv
    conn: aiomysql.Connection = await aiomysql.connect(host, user, password)
    cur: aiomysql.Cursor = await conn.cursor()

    await cur.execute("""
DROP DATABASE IF EXISTS `bot_db`;

CREATE DATABASE `bot_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;

USE
`bot_db`;

CREATE TABLE `users`
(
    id BIGINT NOT NULL PRIMARY KEY,
    state TINYINT NOT NULL DEFAULT -1,
    state_data TEXT NULL
);
create table messages
(
    chat_id bigint not null,
    id int not null auto_increment primary key,
    msg_id int not null,
    text TEXT not null,
    is_bot bool not null
);

create index messages_index
    on messages (chat_id, msg_id);

""")
    await conn.commit()


asyncio.run(migrate())
