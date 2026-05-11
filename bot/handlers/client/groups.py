"""
Client: Bizning guruhlar (TZ §6.5)
Ikki bosqichli ko'rinish: Kategoriya tanlash → Guruhlar ro'yxati → Telegram link
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
from database.crud import group_crud, group_category_crud
from database.database import get_session

logger = logging.getLogger(__name__)
groups_router = Router()


def _localized_name(obj, lang: str) -> str:
    return getattr(obj, f"name_{lang}", None) or obj.name_uz


@groups_router.callback_query(F.data == "client:groups")
async def show_categories(
    callback: CallbackQuery,
    i18n: I18nMiddleware,
) -> None:
    """Faol kategoriyalar ro'yxati"""
    lang = i18n.get_user_language(callback.from_user.id)

    async with get_session() as session:
        categories = await group_category_crud.get_all_active(session)
        # Faqat ichida aktiv guruh bo'lgan kategoriyalarni ko'rsatish
        filtered = []
        for cat in categories:
            cnt = await group_crud.count_by_category(session, cat.id, active_only=True)
            if cnt > 0:
                filtered.append(cat)

    title = i18n.get_text(lang, "groups.title")
    parts = [title, ""]

    if not filtered:
        parts.append(i18n.get_text(lang, "groups.no_groups"))
        await callback.message.edit_text(
            "\n".join(parts),
            reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="client:menu"),
        )
        await callback.answer()
        return

    parts.append(i18n.get_text(lang, "groups.subtitle"))

    rows = []
    for cat in filtered:
        display_name = _localized_name(cat, lang)
        rows.append([
            InlineKeyboardButton(
                text=f"{cat.emoji} {display_name}",
                callback_data=f"cli_cat:{cat.id}",
            ),
        ])
    rows.append([
        InlineKeyboardButton(
            text=i18n.get_text(lang, "buttons.back"),
            callback_data="client:menu",
        ),
    ])

    await callback.message.edit_text(
        "\n".join(parts),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()


@groups_router.callback_query(F.data.startswith("cli_cat:"))
async def show_groups_in_category(
    callback: CallbackQuery,
    i18n: I18nMiddleware,
) -> None:
    """Kategoriya ichidagi faol guruhlar"""
    lang = i18n.get_user_language(callback.from_user.id)

    try:
        cat_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("⚠️", show_alert=True)
        return

    async with get_session() as session:
        category = await group_category_crud.get_by_id(session, cat_id)
        if not category or not category.is_active:
            await callback.answer("⚠️", show_alert=True)
            return
        groups = await group_crud.get_by_category(session, cat_id, active_only=True)

    cat_name = _localized_name(category, lang)
    parts = [
        i18n.get_text(lang, "groups.category_title", name=f"{category.emoji} {cat_name}"),
        "",
    ]

    if not groups:
        parts.append(i18n.get_text(lang, "groups.no_groups_in_category"))
        rows = [[
            InlineKeyboardButton(
                text=i18n.get_text(lang, "buttons.back"),
                callback_data="client:groups",
            ),
        ]]
        await callback.message.edit_text(
            "\n".join(parts),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        )
        await callback.answer()
        return

    parts.append(i18n.get_text(lang, "groups.category_subtitle"))

    rows = []
    for g in groups:
        display_name = _localized_name(g, lang)
        rows.append([
            InlineKeyboardButton(
                text=f"{g.emoji or '📌'} {display_name}",
                url=g.telegram_link,
            ),
        ])
    rows.append([
        InlineKeyboardButton(
            text=i18n.get_text(lang, "buttons.back"),
            callback_data="client:groups",
        ),
    ])

    await callback.message.edit_text(
        "\n".join(parts),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()
