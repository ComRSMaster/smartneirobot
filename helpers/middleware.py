import time

from telebot.asyncio_handler_backends import BaseMiddleware
from telebot.types import Message

from helpers.chat_update import new_user
from helpers.db import BotDB


class ChatManagement(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.update_types = ['message']

    async def pre_process(self, msg: Message, data):
        data['time'] = time.perf_counter()

        user_info = await BotDB.fetchone("SELECT state, state_data FROM users WHERE id = %s", msg.chat.id)
        data['new_user'] = user_info is None
        if data['new_user']:
            msg.state = -1
            await new_user(msg.chat)
        else:
            msg.state = user_info[0]
            data['state_data'] = user_info[1]

    async def post_process(self, message, data, exception):
        print('Время обработки:', time.perf_counter() - data['time'])
