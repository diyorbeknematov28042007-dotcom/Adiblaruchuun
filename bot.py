"""G'afur G'ulom bot — Render web service uchun webhook bilan."""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application,
)
from aiohttp import web

import config
from handlers import get_main_router
from middlewares.subscription import UserContextMiddleware
from utils.scheduler import setup_scheduler
from database import init_tables


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Webhook'ni o'rnatish va schedulerni ishga tushirish."""
    if not config.WEBHOOK_HOST:
        logger.error("WEBHOOK_HOST bo'sh! Render'da to'g'ri qiymat berilganligini tekshiring.")
        return

    webhook_url = config.WEBHOOK_URL
    info = await bot.get_webhook_info()

    if info.url != webhook_url:
        await bot.set_webhook(
            url=webhook_url,
            secret_token=config.WEBHOOK_SECRET,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query", "chat_member", "my_chat_member"],
        )
        logger.info(f"✅ Webhook o'rnatildi: {webhook_url}")
    else:
        logger.info(f"Webhook allaqachon to'g'ri: {webhook_url}")

    setup_scheduler(bot)
    logger.info("✅ Bot ishga tushdi.")


async def on_shutdown(bot: Bot):
    logger.info("Bot to'xtatilmoqda...")
    # webhookni o'chirmaymiz - render qayta ishga tushganda darhol qabul qila olishi uchun


async def health(_request: web.Request) -> web.Response:
    return web.Response(text="OK", status=200)


def create_app() -> web.Application:
    # Tekshirish
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN ko'rsatilmagan!")
    if not config.DATABASE_URL:
        logger.warning("DATABASE_URL ko'rsatilmagan! Baza ishlamaydi.")
    if not config.GEMINI_API_KEYS:
        logger.warning("Gemini API kalitlari yo'q — AI suhbat ishlamaydi.")

    # Jadvallarni yaratish
    init_tables()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares
    dp.update.outer_middleware(UserContextMiddleware())

    # Routers
    dp.include_router(get_main_router())

    # Lifecycle
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    app["bot"] = bot
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    # Webhook handler
    handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=config.WEBHOOK_SECRET,
    )
    handler.register(app, path=config.WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)
    return app


def main():
    app = create_app()
    logger.info(f"Server: {config.WEB_SERVER_HOST}:{config.WEB_SERVER_PORT}")
    web.run_app(
        app,
        host=config.WEB_SERVER_HOST,
        port=config.WEB_SERVER_PORT,
    )


if __name__ == "__main__":
    main()
