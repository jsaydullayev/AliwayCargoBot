"""
Cargo Telegram Bot — entry point (TZ §2.1)
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent

from bot.middlewares.i18n_middleware import init_i18n
from bot.middlewares.role_middleware import role_middleware
from config import settings
from database.crud import get_client_language

# === Routers ===
from bot.handlers.client.onboarding import onboarding_router
from bot.handlers.client.settings import settings_router
from bot.handlers.client.track import track_router
from bot.handlers.client.my_cargo import my_cargo_router
from bot.handlers.client.groups import groups_router as client_groups_router
from bot.handlers.client.contacts import contacts_router

from bot.handlers.manager.admin import admin_router
from bot.handlers.manager.create_cargo import create_cargo_router
from bot.handlers.manager.manage_cargo import manage_cargo_router
from bot.handlers.manager.update_status import update_status_router
from bot.handlers.manager.view_cargos import view_cargos_router
from bot.handlers.manager.export import export_router


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Bot ishga tushirish"""

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Middleware
    dp.update.outer_middleware(role_middleware)

    i18n_mw = init_i18n(get_client_language)
    dp.message.middleware(i18n_mw)
    dp.callback_query.middleware(i18n_mw)

    # === Manager router'lar (avval ulansa, manager filtrlari oldindan ishlaydi) ===
    dp.include_router(admin_router)
    dp.include_router(create_cargo_router)
    dp.include_router(manage_cargo_router)
    dp.include_router(update_status_router)
    dp.include_router(view_cargos_router)
    dp.include_router(export_router)

    # === Client router'lar ===
    dp.include_router(onboarding_router)
    dp.include_router(settings_router)
    dp.include_router(track_router)
    dp.include_router(my_cargo_router)
    dp.include_router(client_groups_router)
    dp.include_router(contacts_router)

    # === Global error handler ===
    @dp.errors()
    async def error_handler(event: ErrorEvent) -> None:
        exception = event.exception
        update = event.update
        logger.error(
            f"Handler xatosi: {type(exception).__name__}: {exception}",
            exc_info=True,
        )

        chat_id = None
        if update.message and update.message.chat:
            chat_id = update.message.chat.id
        elif update.callback_query and update.callback_query.message:
            chat_id = update.callback_query.message.chat.id

        if chat_id:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text="❌ Xato yuz berdi. Iltimos, keyinroq urinib ko'ring yoki /start bosing.",
                )
            except Exception as e:
                logger.error(f"Xato xabarini yuborib bo'lmadi: {e}")

    logger.info("Bot ishga tushmoqda...")
    logger.info(f"Manager IDs: {settings.MANAGER_IDS}")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    asyncio.run(main())
