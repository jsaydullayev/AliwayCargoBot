"""
Client: Bizning guruhlar (TZ §6.5)
"""
import logging

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.keyboards.inline_kb import navigation_keyboard
from bot.middlewares.i18n_middleware import I18nMiddleware
from database.crud import group_crud
from database.database import get_session

logger = logging.getLogger(__name__)
groups_router = Router()


@groups_router.callback_query(F.data == "client:groups")
async def show_groups(
    callback: CallbackQuery,
    i18n: I18nMiddleware,
) -> None:
    """Faol guruhlar ro'yxati"""
    lang = i18n.get_user_language(callback.from_user.id)

    async with get_session() as session:
        groups = await group_crud.get_all_active(session)

    title = i18n.get_text(lang, "groups.title")
    separator = "━━━━━━━━━━━━━━━━━━━━"

    if not groups:
        await callback.message.edit_text(
            f"{title}\n{separator}\n\n{i18n.get_text(lang, 'groups.no_groups')}",
            reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="client:menu"),
        )
        await callback.answer()
        return

    rows = []
    for group in groups:
        name_field = f"name_{lang}"
        group_name = getattr(group, name_field, group.name_uz) or group.name_uz
        rows.append([
            InlineKeyboardButton(
                text=f"{group.emoji or '📌'} {group_name}",
                url=group.telegram_link,
            ),
        ])

    rows.append([
        InlineKeyboardButton(
            text=i18n.get_text(lang, "buttons.back"),
            callback_data="client:menu",
        ),
    ])

    text = (
        f"{title}\n"
        f"{separator}\n\n"
        f"{i18n.get_text(lang, 'groups.subtitle')}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()
