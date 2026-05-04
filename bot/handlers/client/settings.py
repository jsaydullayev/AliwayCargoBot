"""
Client sozlamalari (TZ §9.3) — Til o'zgartirish
"""
import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.keyboards.inline_kb import navigation_keyboard
from bot.middlewares.i18n_middleware import I18nMiddleware
from database.crud import client_crud
from database.database import get_session

logger = logging.getLogger(__name__)
settings_router = Router()


def _language_settings_keyboard(i18n: I18nMiddleware, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="setlang:uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang:ru"),
            InlineKeyboardButton(text="🇹🇷 Türkçe", callback_data="setlang:tr"),
        ],
        [
            InlineKeyboardButton(
                text=i18n.get_text(lang, "buttons.back"),
                callback_data="client:menu",
            ),
        ],
    ])


@settings_router.callback_query(F.data == "client:change_lang")
async def show_change_lang(
    callback: CallbackQuery,
    i18n: I18nMiddleware,
) -> None:
    """Tilni to'g'ridan-to'g'ri o'zgartirish — `client:change_lang`"""
    lang = i18n.get_user_language(callback.from_user.id)
    await callback.message.edit_text(
        f"🌐 <b>{i18n.get_text(lang, 'change_language.title')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{i18n.get_text(lang, 'change_language.select_language')}",
        reply_markup=_language_settings_keyboard(i18n, lang),
    )
    await callback.answer()


@settings_router.callback_query(F.data == "client:settings")
async def show_settings(
    callback: CallbackQuery,
    i18n: I18nMiddleware,
) -> None:
    """Sozlamalar menyusi — til o'zgartirish"""
    lang = i18n.get_user_language(callback.from_user.id)

    lang_labels = {
        "uz": "🇺🇿 O'zbek",
        "ru": "🇷🇺 Русский",
        "tr": "🇹🇷 Türkçe",
    }
    current_label = lang_labels.get(lang, lang)

    text = (
        f"{i18n.get_text(lang, 'settings.title')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{i18n.get_text(lang, 'change_language.select_language')}\n\n"
        f"{i18n.get_text(lang, 'settings.current_language')} <b>{current_label}</b>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=_language_settings_keyboard(i18n, lang),
    )
    await callback.answer()


@settings_router.callback_query(F.data.startswith("setlang:"))
async def set_language(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Tilni o'zgartirish (client va manager uchun ham)"""
    new_lang = callback.data.split(":")[1]

    if new_lang not in ("uz", "ru", "tr"):
        await callback.answer("⚠️", show_alert=True)
        return

    user_id = callback.from_user.id

    async with get_session() as session:
        client = await client_crud.get_by_telegram_id(session, user_id)
        if client:
            await client_crud.update_language(session, user_id, new_lang)
            await session.commit()

    # Cache yangilash
    i18n._cache[user_id] = new_lang

    await callback.message.edit_text(
        i18n.get_text(new_lang, "change_language.changed"),
        reply_markup=navigation_keyboard(
            lang=new_lang,
            i18n=i18n,
            back_callback="client:menu",
        ),
    )
    await callback.answer()


# `lang:` callback ham qo'llanadi (onboarding va manager change_lang uchun)
@settings_router.callback_query(F.data.startswith("lang:"))
async def lang_callback_compat(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """`lang:` callback (manager change_lang sahifasidan) — tilni o'zgartirish"""
    # OnboardingStates ichida bo'lsa, onboarding'ga o'tadi (state'li handler birinchi yutadi)
    new_lang = callback.data.split(":")[1]

    if new_lang not in ("uz", "ru", "tr"):
        await callback.answer("⚠️", show_alert=True)
        return

    user_id = callback.from_user.id

    async with get_session() as session:
        client = await client_crud.get_by_telegram_id(session, user_id)
        if client:
            await client_crud.update_language(session, user_id, new_lang)
            await session.commit()

    i18n._cache[user_id] = new_lang

    from config import settings as app_settings
    if user_id in app_settings.MANAGER_IDS:
        from bot.handlers.manager.admin import manager_main_keyboard
        await callback.message.edit_text(
            f"{i18n.get_text(new_lang, 'change_language.changed')}\n\n"
            f"📊 <b>{i18n.get_text(new_lang, 'manager_menu.title')}</b>",
            reply_markup=manager_main_keyboard(i18n, new_lang),
        )
    else:
        from bot.handlers.client.onboarding import client_main_keyboard
        await callback.message.edit_text(
            i18n.get_text(new_lang, "change_language.changed"),
            reply_markup=client_main_keyboard(i18n, new_lang),
        )
    await callback.answer()
