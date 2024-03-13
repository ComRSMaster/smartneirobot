import asyncio
import time
from asyncio import ensure_future, Task

import g4f
from telebot.asyncio_helper import ApiTelegramException, logger
from telebot.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telebot.util import quick_markup, escape

from helpers.bot import bot
from helpers.db import BotDB
from helpers.user_states import States
import nest_asyncio


async def send_status_periodic(chat_id, status):
    while True:
        await bot.send_chat_action(chat_id, status)
        await asyncio.sleep(5)


def get_stop_markup(task_id):
    return quick_markup({'🛑 Стоп': {'callback_data': f'ai_stop_{task_id}'}})


async def reset_context(chat_id):
    await BotDB.execute("DELETE FROM messages WHERE chat_id = %s", chat_id)


generating_tasks: dict[str, Task] = {}

g4f.debug.version_check = False
models = {"ChatGPT 3.5": g4f.models.gpt_35_turbo,
          "Llama2": g4f.models.llama2_70b,
          "CodeLlama": g4f.models.codellama_70b_instruct,
          "GeminiPro": g4f.models.gemini_pro}

list_models = list(models)


class AiTalk:
    @bot.message_handler(['cancel'], state=States.AI_TALK)
    async def command_cancel(msg: Message):
        await bot.send_message(msg.chat.id, "<b>Переписка окончена</b>", reply_markup=ReplyKeyboardRemove())
        await reset_context(msg.chat.id)
        await BotDB.set_state(msg.chat.id, -1)

    @bot.message_handler(['start'])
    async def command_cancel(msg: Message):
        markup = ReplyKeyboardMarkup()
        markup.add(*list_models)
        if msg.state == States.AI_TALK:
            await reset_context(msg.chat.id)
            await bot.send_message(msg.chat.id, "<b>Контекст сброшен</b>", reply_markup=markup)
        else:
            await bot.send_message(msg.chat.id,
                                   f"<b>Привет, {escape(msg.chat.title or msg.chat.first_name)}</b>",
                                   reply_markup=markup)
        await BotDB.set_state(msg.chat.id, States.AI_TALK, g4f.models.gpt_35_turbo.name)

    @bot.message_handler(['delete'], state=States.AI_TALK, is_reply=True)
    async def command_cancel(msg: Message):
        await bot.reply_to(msg.reply_to_message, "<b>Сообщение удалено из контекста</b>")
        await BotDB.execute("DELETE FROM messages WHERE chat_id = %s AND msg_id = %s",
                            (msg.chat.id, msg.reply_to_message.id))

    @bot.message_handler(['delete'])
    async def command_cancel(msg: Message):
        await bot.reply_to(msg.reply_to_message,
                           "<b>Чтобы удалить сообщение из контекста, ответьте на него этой командой во время диалога</b>")

    @bot.message_handler(state=States.AI_TALK, content_types=['text'])
    async def command_cancel(msg: Message, data: dict):
        if msg.text in list_models:
            await bot.send_message(msg.chat.id, f"Выбрана модель: <b>{msg.text}</b>")
            await BotDB.set_state(msg.chat.id, States.AI_TALK, msg.text)
            return

        raw_messages = await BotDB.fetchall(
            "SELECT text, is_bot FROM messages WHERE chat_id = %s", msg.chat.id)
        messages = [{"role": "assistant" if is_bot else "user", "content": text} for text, is_bot in raw_messages]
        messages.append({"role": "user", "content": msg.text})

        print(raw_messages, messages)

        loop = asyncio.get_event_loop()

        async def generating_task():
            msg_id = None
            status_task = None
            all_result = ''
            curr_result = ''
            prev_result = ''
            prev_time = 0

            async def send_to_user(use_md=True):
                nonlocal msg_id, status_task, prev_result
                if prev_result == curr_result:
                    return
                if msg_id is None:
                    prev_result = curr_result
                    msg_id = (await bot.send_message(
                        msg.chat.id, curr_result, 'Markdown' if use_md else '', reply_markup=stop_markup)).id
                    if status_task is None:
                        status_task = loop.create_task(send_status_periodic(msg.chat.id, 'typing'))
                else:
                    # print(curr_result, chat_id, msg_id)
                    prev_result = curr_result
                    await bot.edit_message_text(
                        curr_result, msg.chat.id, msg_id,
                        parse_mode='Markdown' if use_md else '', reply_markup=stop_markup)

            try:
                nest_asyncio.apply()
                for text in g4f.ChatCompletion.create(
                        model=models[data['state_data']],
                        messages=messages,
                        stream=True):

                    print(text)
                    all_result += text
                    if len(curr_result + text) > 4096:
                        # await bot.edit_message_reply_markup(chat_id, msg_id)
                        msg_id = None
                        curr_result = text
                    else:
                        curr_result += text

                    if text == '':
                        continue

                    curr_time = time.time()
                    if curr_time - prev_time < 1 and msg_id is not None:  # cooldown 1 second
                        continue
                    prev_time = curr_time

                    try:
                        await send_to_user(False)
                    except ApiTelegramException as e:
                        logger.error(e)
                        continue
            except asyncio.CancelledError:
                print('STOP')
                return all_result, msg_id
            finally:
                try:
                    await send_to_user(True)
                except ApiTelegramException as e:
                    logger.error(e)
                if status_task is not None:
                    status_task.cancel()
            ensure_future(bot.edit_message_reply_markup(msg.chat.id, msg_id))
            return all_result, msg_id

        gen_task = loop.create_task(generating_task())
        generating_tasks[gen_task.get_name()] = gen_task

        stop_markup = get_stop_markup(gen_task.get_name())

        await BotDB.execute(
            "INSERT INTO messages SET chat_id = %s, msg_id = %s, text = %s, is_bot = 0;",
            (msg.chat.id, msg.id, msg.text))

        result, new_msg_id = await gen_task

        await BotDB.execute(
            "INSERT INTO messages SET chat_id = %s, msg_id = %s, text = %s, is_bot = 1;",
            (msg.chat.id, new_msg_id, result))
