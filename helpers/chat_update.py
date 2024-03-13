from os.path import isfile

from telebot.util import escape

from helpers.bot import bot
from helpers.config import admin_chat
from helpers.db import BotDB
from telebot.types import Chat, Message, ChatMemberUpdated


class ChatUpdater:
    @bot.message_handler(content_types=["migrate_to_chat_id"])
    async def migrate_to_chat_id(msg: Message):
        await BotDB.execute("UPDATE users SET id = %s WHERE id = %s", (msg.migrate_to_chat_id, msg.chat.id))

    @bot.my_chat_member_handler(None)
    async def ban_handler(member: ChatMemberUpdated):
        if member.new_chat_member.status in ["restricted", "kicked", "left"]:
            await delete_chat(member.chat.id)


async def new_user(chat: Chat):
    await BotDB.execute("INSERT INTO users SET id = %s", chat.id)

    await bot.send_message(
        admin_chat,
        f"<b>Новый пользователь:\n"
        f"<a href='tg://user?id={chat.id}'>{escape(chat.first_name + ' ' + chat.last_name)}</a>\n"
        f"{('@' + chat.username) if chat.username else ''}\n<code>{chat.id}</code></b>"

        if chat.type == "private" else

        f"<b>Новая группа:\n{escape(chat.title)}\n<code>{chat.id}</code></b>")


async def delete_chat(chat_id):
    await BotDB.execute("DELETE FROM users WHERE id = %s", chat_id)
    await bot.send_message(admin_chat, f"<b>Удалён чат:  <code>{chat_id}</code></b>")
