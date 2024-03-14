import ujson
from telebot.types import Update, Message

from aiohttp import web
from telebot.util import quick_markup

from functions.ai_draw import AiDraw
from functions.ai_talk import AiTalk
from functions.ai_upscale import AiUpscale
from functions.ai_voice import AiVoice
from functions.cmd_handler import CmdHandler
from helpers import session_manager, config
from helpers.bot import bot
from helpers.chat_update import ChatUpdater
from helpers.db import BotDB
from pathlib import Path

AiDraw()
AiTalk()
AiUpscale()
AiVoice()
CmdHandler()
ChatUpdater()

routes = web.RouteTableDef()

static_dir_path = Path('website')


async def shutdown(app):
    await bot.close_session()

    if BotDB.pool is not None:
        await BotDB.pool.clear()

    await session_manager.close_all_sessions()
    print("server stopped")


async def app_factory():
    app = web.Application()
    app.add_routes(routes)
    app.on_shutdown.append(shutdown)
    return app


@routes.post('/tg_webhook')
async def webhook_endpoint(request: web.Request):
    if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != config.webhook_token:
        return web.Response(status=403)

    data = await request.json(loads=ujson.loads)
    await bot.process_new_updates([Update.de_json(data)])
    return web.Response()


async def set_webhook():
    await bot.set_webhook(url=config.web_url + 'tg_webhook', secret_token=config.webhook_token)


# Запуск бота
if config.is_dev:
    print("polling started")
    BotDB.loop.run_until_complete(bot.infinity_polling())
else:
    BotDB.loop.run_until_complete(set_webhook())
    print("server started")
    web.run_app(app_factory(), host=config.host, port=config.port)
