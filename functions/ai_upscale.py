from telebot.types import Message, ReplyKeyboardRemove
from telebot.util import quick_markup

from helpers.bot import bot
from helpers.db import BotDB


class AiUpscale:
    @bot.message_handler(['cancel'], state='*')
    async def command_cancel(msg: Message):
        await bot.send_message(msg.chat.id, "<b>Всё отменяю</b>", reply_markup=ReplyKeyboardRemove())
        await BotDB.set_state(msg.chat.id, -1)
