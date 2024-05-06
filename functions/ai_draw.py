import asyncio
import base64

import aiohttp
import requests
import ujson
from telebot.types import Message
from telebot.util import extract_arguments
from g4f.client import Client

from helpers.bot import bot
from helpers.config import fb_api_key, fb_secret

AUTH_HEADERS = {
    'X-Key': f'Key {fb_api_key}',
    'X-Secret': f'Secret {fb_secret}',
}
URL = 'https://api-key.fusionbrain.ai/'


async def get_model():
    async with aiohttp.request('GET', url=URL + 'key/api/v1/models', headers=AUTH_HEADERS) as response:
        data = await response.json()
        return data[0]['id']


async def generate(prompt, model=4, images=1, width=1024, height=1024):
    params = {
        "type": "GENERATE",
        "numImages": images,
        "width": width,
        "height": height,
        "generateParams": {
            "query": f"{prompt}"
        }
    }

    data = {
        'model_id': (None, model),
        'params': (None, ujson.dumps(params), 'application/json')
    }
    response = requests.post(URL + 'key/api/v1/text2image/run', headers=AUTH_HEADERS, files=data)
    data = response.json()
    return data['uuid']


async def check_generation(request_id, chat_id, attempts=15, delay=5):
    while attempts > 0:
        async with aiohttp.request(
                'GET', url=URL + 'key/api/v1/text2image/status/' + request_id, headers=AUTH_HEADERS) as response:
            if response.status != 200:
                return
            data = await response.json()
            if data['status'] == 'DONE':
                return data['images']
            elif data['status'] == 'FAIL':
                print(data['errorDescription'])
                return

        attempts -= 1
        await bot.send_chat_action(chat_id, 'upload_photo')
        await asyncio.sleep(delay)


class AiDraw:
    @bot.message_handler(['draw'])
    async def command_cancel(msg: Message):
        args = extract_arguments(msg.text)
        if not args:
            await bot.send_message(msg.chat.id, "<b>Используйте команду так:\n<pre>/draw запрос</pre></b>")
            return

        await bot.send_chat_action(msg.chat.id, 'upload_photo')

        uuid = await generate(args)
        if uuid is None:
            await bot.send_message(msg.chat.id, "<b>Возникла ошибка</b>")
            return

        images = await check_generation(uuid, msg.chat.id)
        if images is None:
            await bot.send_message(msg.chat.id, "<b>Возникла ошибка</b>")
            return

        await bot.send_photo(msg.chat.id, base64.b64decode(images[0]), reply_to_message_id=msg.id)
