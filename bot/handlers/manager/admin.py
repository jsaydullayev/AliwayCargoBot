"""
Manager admin paneli (TZ §5.1)
/admin yoki callback'lar orqali kiriladi
"""
import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command, CommandStart

from bot.middlewares.i18n_middleware import I18nMiddleware
from config import settings

logger = logging.getLogger(__name__)
admin_router = Router()


def manager_main_keyboard(i18n: I18nMiddleware, lang: str) -> InlineKeyboardMarkup:
    """Manager asosiy menyu klaviaturasi — 2 ustunli (TZ §5.1)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=i18n.get_text(lang, "manager_menu.buttons.create_cargo"),
                callback_data="manager:create_cargo",
            ),
            InlineKeyboardButton(
                text=i18n.get_text(lang, "manager_menu.buttons.manage_cargo"),
                callback_data="manager:manage_cargo",
            ),
        ],
        [
            InlineKeyboardButton(
                text=i18n.get_text(lang, "manager_menu.buttons.update_status"),
                callback_data="manager:update_status",
            ),
            InlineKeyboardButton(
                text=i18n.get_text(lang, "manager_menu.buttons.view_cargos"),
                callback_data="manager:view_cargos",
            ),
        ],
        [
            InlineKeyboardButton(
                text=i18n.get_text(lang, "manager_menu.buttons.export"),
                callback_data="manager:export",
            ),
            InlineKeyboardButton(
                text=i18n.get_text(lang, "buttons.change_language"),
                callback_data="manager:change_lang",
            ),
        ],
    ])


def _is_manager(user_id: int) -> bool:
    return user_id in settings.MANAGER_IDS


@admin_router.message(Command("admin"))
async def admin_panel_command(
    message: Message,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """`/admin` komandasi orqali manager menyuni ochish"""
    if not _is_manager(message.from_user.id):
        lang = i18n.get_user_language(message.from_user.id)
        await message.answer(i18n.get_text(lang, "errors.no_permission"))
        return

    await state.clear()
    lang = i18n.get_user_language(message.from_user.id)
    await message.answer(
        f"📊 <b>{i18n.get_text(lang, 'manager_menu.title')}</b>\n\n"
        f"{i18n.get_text(lang, 'manager_menu.select_action')}",
        reply_markup=manager_main_keyboard(i18n, lang),
    )


@admin_router.callback_query(F.data == "manager:menu")
async def manager_menu_callback(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Manager menyuga qaytish (callback)"""
    if not _is_manager(callback.from_user.id):
        lang = i18n.get_user_language(callback.from_user.id)
        await callback.answer(i18n.get_text(lang, "errors.no_permission"), show_alert=True)
        return

    await state.clear()
    lang = i18n.get_user_language(callback.from_user.id)
    await callback.message.edit_text(
        f"📊 <b>{i18n.get_text(lang, 'manager_menu.title')}</b>\n\n"
        f"{i18n.get_text(lang, 'manager_menu.select_action')}",
        reply_markup=manager_main_keyboard(i18n, lang),
    )
    await callback.answer()


@admin_router.callback_query(F.data == "manager:change_lang")
async def manager_change_lang(
    callback: CallbackQuery,
    i18n: I18nMiddleware,
) -> None:
    """Manager uchun til o'zgartirish menyusi"""
    from bot.keyboards.inline_kb import language_selection_keyboard

    lang = i18n.get_user_language(callback.from_user.id)
    await callback.message.edit_text(
        i18n.get_text(lang, "change_language.select_language"),
        reply_markup=language_selection_keyboard(),
    )
    await callback.answer()


@admin_router.message(CommandStart(), F.from_user.id.in_(settings.MANAGER_IDS))
async def manager_start(
    message: Message,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Manager `/start` bossa — to'g'ridan manager menyu"""
    await state.clear()
    lang = i18n.get_user_language(message.from_user.id)
    await message.answer(
        f"👋 <b>Salom, {message.from_user.full_name}!</b>\n\n"
        f"📊 <b>{i18n.get_text(lang, 'manager_menu.title')}</b>\n\n"
        f"{i18n.get_text(lang, 'manager_menu.select_action')}",
        reply_markup=manager_main_keyboard(i18n, lang),
    )
