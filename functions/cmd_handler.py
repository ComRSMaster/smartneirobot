from telebot.types import Message, ReplyKeyboardRemove
from telebot.util import quick_markup

from helpers.bot import bot
from helpers.db import BotDB


class CmdHandler:
    @bot.message_handler(['cancel'], state='*')
    async def command_cancel(msg: Message):
        await bot.send_message(msg.chat.id, "<b>Всё отменяю</b>", reply_markup=ReplyKeyboardRemove())
        await BotDB.set_state(msg.chat.id, -1)

    @bot.message_handler(['cancel'], state=-1)
    async def command_cancel(msg: Message):
        await bot.send_message(msg.chat.id, "<b>Нечего отменять</b>", reply_markup=ReplyKeyboardRemove())

    @bot.message_handler(content_types=['photo'])
    async def chatting(msg: Message):
        await bot.reply_to(msg, "<b>Что сделать с этим фото?</b>",
                           reply_markup=quick_markup(
                               {'Улучшить качество': {'callback_data': 'upscale'}}))

    @bot.message_handler(content_types=['document'])
    async def chatting(msg: Message):
        await bot.reply_to(msg, "<b>Что сделать с этим файлом?</b>",
                           reply_markup=quick_markup(
                               {'Улучшить качество фото': {'callback_data': 'upscale'}}))

    @bot.message_handler(content_types=['voice'])
    async def chatting(msg: Message):
        await bot.reply_to(msg, "<b>Что сделать с этим голосовым сообщением?</b>",
                           reply_markup=quick_markup(
                               {'Расшифровать': {'callback_data': 'decode'}}))

    @bot.message_handler(content_types=['audio'])
    async def chatting(msg: Message):
        await bot.reply_to(msg, "<b>Что сделать с этой записью?</b>",
                           reply_markup=quick_markup(
                               {'Расшифровать': {'callback_data': 'decode'}}))

    @bot.message_handler(state=-1, content_types=['text'])
    async def chatting(msg: Message):
        await bot.reply_to(msg, "<b>Что сделать с этим запросом?</b>",
                           reply_markup=quick_markup(
                               {'Ответить с помощью ChatGPT': {'callback_data': 'chatgpt'},
                                'Нарисовать картинку': {'callback_data': 'draw'}},
                               row_width=1))
