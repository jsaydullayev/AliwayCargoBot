"""
Manager: Guruh va kategoriyalarni boshqarish (TZ §4.4)
Ierarxiya: Kategoriya (masalan: Erkaklar kiyimi) → Guruhlar (Premium, Economy, ...)
"""
import logging
import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command

from bot.keyboards.inline_kb import confirm_keyboard, navigation_keyboard
from bot.middlewares.i18n_middleware import I18nMiddleware
from database.crud import group_crud, group_category_crud
from database.database import get_session

logger = logging.getLogger(__name__)
groups_admin_router = Router()

SEPARATOR = "━━━━━━━━━━━━━━━━━━━━"
TELEGRAM_LINK_RE = re.compile(
    r"^(https?://)?(t\.me|telegram\.me)/(\+?[\w\-/]+|joinchat/[\w\-]+)/?$",
    re.IGNORECASE,
)


class AddGroupStates(StatesGroup):
    selecting_category = State()
    input_emoji = State()
    input_name_uz = State()
    input_name_ru = State()
    input_name_tr = State()
    input_link = State()
    confirming = State()


class AddCategoryStates(StatesGroup):
    input_emoji = State()
    input_name_uz = State()
    input_name_ru = State()
    input_name_tr = State()
    confirming = State()


# ============== Utility ==============

def _skip_cancel_keyboard(i18n: I18nMiddleware, lang: str, cancel_cb: str = "grp:cancel") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.get_text(lang, "buttons.skip"), callback_data="grp:skip")],
        [InlineKeyboardButton(text=i18n.get_text(lang, "buttons.cancel"), callback_data=cancel_cb)],
    ])


def _cancel_keyboard(i18n: I18nMiddleware, lang: str, cancel_cb: str = "grp:cancel") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.get_text(lang, "buttons.cancel"), callback_data=cancel_cb)],
    ])


def _normalize_link(text: str) -> str | None:
    """Telegram havolasini tekshirish va normalizatsiya"""
    cleaned = (text or "").strip()
    if not cleaned:
        return None
    if cleaned.startswith("@") and re.fullmatch(r"@[\w]+", cleaned):
        return f"https://t.me/{cleaned[1:]}"
    if not TELEGRAM_LINK_RE.match(cleaned):
        return None
    if not cleaned.lower().startswith(("http://", "https://")):
        cleaned = f"https://{cleaned}"
    return cleaned


def _localized_name(obj, lang: str) -> str:
    """Lokallashtirilgan nomni olish"""
    return getattr(obj, f"name_{lang}", None) or obj.name_uz


# ============== Bosh sahifa — kategoriyalar ro'yxati ==============

@groups_admin_router.callback_query(F.data == "manager:groups")
async def groups_admin_menu(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Kategoriyalar ro'yxati + yangi kategoriya/guruh qo'shish tugmalari"""
    lang = i18n.get_user_language(callback.from_user.id)
    await state.clear()

    async with get_session() as session:
        categories = await group_category_crud.get_all(session)
        groups_count_map = {}
        for cat in categories:
            groups_count_map[cat.id] = await group_crud.count_by_category(session, cat.id, active_only=False)

    parts = [
        i18n.get_text(lang, "groups_admin.title"),
        SEPARATOR,
        "",
    ]

    if not categories:
        parts.append(i18n.get_text(lang, "groups_admin.no_categories"))
    else:
        parts.append(i18n.get_text(lang, "groups_admin.categories_section"))
        parts.append("")
        for idx, cat in enumerate(categories, start=1):
            status_icon = "✅" if cat.is_active else "⏸"
            display_name = _localized_name(cat, lang)
            cnt = groups_count_map.get(cat.id, 0)
            parts.append(f"{idx}. {status_icon} {cat.emoji} <b>{display_name}</b> ({cnt})")

    rows = []
    # Kategoriyalar inline tugmalari (faqat mavjud bo'lsa)
    for cat in categories:
        display_name = _localized_name(cat, lang)
        rows.append([
            InlineKeyboardButton(
                text=f"{cat.emoji} {display_name}",
                callback_data=f"grp_cat:view:{cat.id}",
            ),
        ])

    rows.append([
        InlineKeyboardButton(
            text=i18n.get_text(lang, "groups_admin.add_category_button"),
            callback_data="grp_cat:add",
        ),
    ])
    if categories:
        rows.append([
            InlineKeyboardButton(
                text=i18n.get_text(lang, "groups_admin.add_group_button"),
                callback_data="grp:add",
            ),
        ])
    rows.append([
        InlineKeyboardButton(
            text=i18n.get_text(lang, "buttons.back"),
            callback_data="manager:menu",
        ),
    ])

    await callback.message.edit_text(
        "\n".join(parts),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()


# ============== Kategoriya ko'rinishi (ichidagi guruhlar) ==============

@groups_admin_router.callback_query(F.data.startswith("grp_cat:view:"))
async def view_category(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    lang = i18n.get_user_language(callback.from_user.id)
    await state.clear()

    try:
        cat_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("⚠️", show_alert=True)
        return

    async with get_session() as session:
        category = await group_category_crud.get_by_id(session, cat_id)
        if not category:
            await callback.answer("⚠️ Kategoriya topilmadi", show_alert=True)
            return
        groups = await group_crud.get_by_category(session, cat_id, active_only=False)

    name = _localized_name(category, lang)
    parts = [
        i18n.get_text(lang, "groups_admin.category_view_title", name=f"{category.emoji} {name}"),
        SEPARATOR,
        "",
    ]
    if not groups:
        parts.append(i18n.get_text(lang, "groups_admin.no_groups_in_category"))
    else:
        parts.append(i18n.get_text(lang, "groups_admin.groups_in_category"))
        parts.append("")
        for idx, g in enumerate(groups, start=1):
            status_icon = "✅" if g.is_active else "⏸"
            display_name = _localized_name(g, lang)
            parts.append(f"{idx}. {status_icon} {g.emoji or '📌'} <b>{display_name}</b>")
            parts.append(f"   🔗 {g.telegram_link}")

    rows = [
        [
            InlineKeyboardButton(
                text=i18n.get_text(lang, "groups_admin.add_group_button"),
                callback_data=f"grp:add_in:{cat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=i18n.get_text(lang, "buttons.back"),
                callback_data="manager:groups",
            ),
        ],
    ]

    await callback.message.edit_text(
        "\n".join(parts),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()


# ============== KATEGORIYA QO'SHISH ==============

@groups_admin_router.callback_query(F.data == "grp_cat:add")
async def add_category_start(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    lang = i18n.get_user_language(callback.from_user.id)
    await state.clear()
    await state.set_state(AddCategoryStates.input_emoji)
    await callback.message.edit_text(
        i18n.get_text(lang, "groups_admin.category_input_emoji"),
        reply_markup=_skip_cancel_keyboard(i18n, lang, cancel_cb="grp_cat:cancel"),
    )
    await callback.answer()


@groups_admin_router.message(AddCategoryStates.input_emoji)
async def category_emoji_input(message: Message, state: FSMContext, i18n: I18nMiddleware) -> None:
    lang = i18n.get_user_language(message.from_user.id)
    emoji = (message.text or "").strip()
    if len(emoji) > 10:
        await message.answer(i18n.get_text(lang, "groups_admin.invalid_emoji"))
        return
    await state.update_data(emoji=emoji or "📂")
    await state.set_state(AddCategoryStates.input_name_uz)
    await message.answer(
        i18n.get_text(lang, "groups_admin.category_input_name_uz"),
        reply_markup=_cancel_keyboard(i18n, lang, cancel_cb="grp_cat:cancel"),
    )


@groups_admin_router.message(AddCategoryStates.input_name_uz)
async def category_name_uz_input(message: Message, state: FSMContext, i18n: I18nMiddleware) -> None:
    lang = i18n.get_user_language(message.from_user.id)
    name = (message.text or "").strip()
    if not name:
        await message.answer(i18n.get_text(lang, "groups_admin.invalid_name"))
        return
    await state.update_data(name_uz=name)
    await state.set_state(AddCategoryStates.input_name_ru)
    await message.answer(
        i18n.get_text(lang, "groups_admin.category_input_name_ru"),
        reply_markup=_cancel_keyboard(i18n, lang, cancel_cb="grp_cat:cancel"),
    )


@groups_admin_router.message(AddCategoryStates.input_name_ru)
async def category_name_ru_input(message: Message, state: FSMContext, i18n: I18nMiddleware) -> None:
    lang = i18n.get_user_language(message.from_user.id)
    name = (message.text or "").strip()
    if not name:
        await message.answer(i18n.get_text(lang, "groups_admin.invalid_name"))
        return
    await state.update_data(name_ru=name)
    await state.set_state(AddCategoryStates.input_name_tr)
    await message.answer(
        i18n.get_text(lang, "groups_admin.category_input_name_tr"),
        reply_markup=_cancel_keyboard(i18n, lang, cancel_cb="grp_cat:cancel"),
    )


@groups_admin_router.message(AddCategoryStates.input_name_tr)
async def category_name_tr_input(message: Message, state: FSMContext, i18n: I18nMiddleware) -> None:
    lang = i18n.get_user_language(message.from_user.id)
    name = (message.text or "").strip()
    if not name:
        await message.answer(i18n.get_text(lang, "groups_admin.invalid_name"))
        return
    await state.update_data(name_tr=name)
    await state.set_state(AddCategoryStates.confirming)
    data = await state.get_data()
    preview = i18n.get_text(
        lang,
        "groups_admin.category_preview",
        emoji=data.get("emoji", "📂"),
        name_uz=data.get("name_uz", "—"),
        name_ru=data.get("name_ru", "—"),
        name_tr=name,
    )
    await message.answer(
        preview,
        reply_markup=confirm_keyboard(
            lang=lang, i18n=i18n,
            confirm_callback="grp_cat:confirm",
            cancel_callback="grp_cat:cancel",
        ),
    )


@groups_admin_router.callback_query(F.data == "grp_cat:confirm")
async def category_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    lang = i18n.get_user_language(callback.from_user.id)
    data = await state.get_data()

    if not all([data.get("name_uz"), data.get("name_ru"), data.get("name_tr")]):
        await callback.answer(i18n.get_text(lang, "errors.session_expired"), show_alert=True)
        await state.clear()
        return

    async with get_session() as session:
        category = await group_category_crud.create(
            session=session,
            name_uz=data["name_uz"],
            name_ru=data["name_ru"],
            name_tr=data["name_tr"],
            emoji=data.get("emoji", "📂"),
        )
        await session.commit()
        cat_id = category.id
        saved_name = data["name_uz"]

    logger.info(f"Kategoriya qo'shildi — Manager: {callback.from_user.id}, ID: {cat_id}, Name: {saved_name}")

    await callback.message.edit_text(
        i18n.get_text(lang, "groups_admin.category_saved", name=saved_name),
        reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="manager:groups"),
    )
    await callback.answer()
    await state.clear()


@groups_admin_router.callback_query(F.data == "grp_cat:cancel")
async def category_cancel(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    lang = i18n.get_user_language(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(
        i18n.get_text(lang, "groups_admin.cancelled"),
        reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="manager:groups"),
    )
    await callback.answer()


# ============== GURUH QO'SHISH ==============

@groups_admin_router.callback_query(F.data == "grp:add")
async def add_group_start(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Yangi guruh qo'shish — kategoriyani tanlash"""
    lang = i18n.get_user_language(callback.from_user.id)
    await state.clear()

    async with get_session() as session:
        categories = await group_category_crud.get_all_active(session)

    if not categories:
        await callback.answer(i18n.get_text(lang, "groups_admin.no_categories"), show_alert=True)
        return

    await state.set_state(AddGroupStates.selecting_category)

    rows = []
    for cat in categories:
        display_name = _localized_name(cat, lang)
        rows.append([
            InlineKeyboardButton(
                text=f"{cat.emoji} {display_name}",
                callback_data=f"grp:cat_chosen:{cat.id}",
            ),
        ])
    rows.append([
        InlineKeyboardButton(
            text=i18n.get_text(lang, "buttons.cancel"),
            callback_data="grp:cancel",
        ),
    ])

    await callback.message.edit_text(
        i18n.get_text(lang, "groups_admin.select_category_for_group"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()


@groups_admin_router.callback_query(F.data.startswith("grp:add_in:"))
async def add_group_in_category(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Kategoriya ko'rinishidan to'g'ridan-to'g'ri guruh qo'shish"""
    lang = i18n.get_user_language(callback.from_user.id)
    await state.clear()

    try:
        cat_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("⚠️", show_alert=True)
        return

    async with get_session() as session:
        category = await group_category_crud.get_by_id(session, cat_id)
        if not category or not category.is_active:
            await callback.answer("⚠️", show_alert=True)
            return
        cat_name = _localized_name(category, lang)

    await state.set_state(AddGroupStates.input_emoji)
    await state.update_data(category_id=cat_id, category_name=cat_name)

    await callback.message.edit_text(
        i18n.get_text(lang, "groups_admin.input_emoji"),
        reply_markup=_skip_cancel_keyboard(i18n, lang),
    )
    await callback.answer()


@groups_admin_router.callback_query(
    AddGroupStates.selecting_category,
    F.data.startswith("grp:cat_chosen:"),
)
async def group_category_chosen(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    lang = i18n.get_user_language(callback.from_user.id)
    try:
        cat_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("⚠️", show_alert=True)
        return

    async with get_session() as session:
        category = await group_category_crud.get_by_id(session, cat_id)
        if not category:
            await callback.answer("⚠️", show_alert=True)
            return
        cat_name = _localized_name(category, lang)

    await state.update_data(category_id=cat_id, category_name=cat_name)
    await state.set_state(AddGroupStates.input_emoji)
    await callback.message.edit_text(
        i18n.get_text(lang, "groups_admin.input_emoji"),
        reply_markup=_skip_cancel_keyboard(i18n, lang),
    )
    await callback.answer()


@groups_admin_router.message(AddGroupStates.input_emoji)
async def group_emoji_input(message: Message, state: FSMContext, i18n: I18nMiddleware) -> None:
    lang = i18n.get_user_language(message.from_user.id)
    emoji = (message.text or "").strip()
    if len(emoji) > 10:
        await message.answer(i18n.get_text(lang, "groups_admin.invalid_emoji"))
        return
    await state.update_data(emoji=emoji or "📌")
    await state.set_state(AddGroupStates.input_name_uz)
    await message.answer(
        i18n.get_text(lang, "groups_admin.input_name_uz"),
        reply_markup=_cancel_keyboard(i18n, lang),
    )


@groups_admin_router.message(AddGroupStates.input_name_uz)
async def group_name_uz_input(message: Message, state: FSMContext, i18n: I18nMiddleware) -> None:
    lang = i18n.get_user_language(message.from_user.id)
    name = (message.text or "").strip()
    if not name:
        await message.answer(i18n.get_text(lang, "groups_admin.invalid_name"))
        return
    await state.update_data(name_uz=name)
    await state.set_state(AddGroupStates.input_name_ru)
    await message.answer(
        i18n.get_text(lang, "groups_admin.input_name_ru"),
        reply_markup=_cancel_keyboard(i18n, lang),
    )


@groups_admin_router.message(AddGroupStates.input_name_ru)
async def group_name_ru_input(message: Message, state: FSMContext, i18n: I18nMiddleware) -> None:
    lang = i18n.get_user_language(message.from_user.id)
    name = (message.text or "").strip()
    if not name:
        await message.answer(i18n.get_text(lang, "groups_admin.invalid_name"))
        return
    await state.update_data(name_ru=name)
    await state.set_state(AddGroupStates.input_name_tr)
    await message.answer(
        i18n.get_text(lang, "groups_admin.input_name_tr"),
        reply_markup=_cancel_keyboard(i18n, lang),
    )


@groups_admin_router.message(AddGroupStates.input_name_tr)
async def group_name_tr_input(message: Message, state: FSMContext, i18n: I18nMiddleware) -> None:
    lang = i18n.get_user_language(message.from_user.id)
    name = (message.text or "").strip()
    if not name:
        await message.answer(i18n.get_text(lang, "groups_admin.invalid_name"))
        return
    await state.update_data(name_tr=name)
    await state.set_state(AddGroupStates.input_link)
    await message.answer(
        i18n.get_text(lang, "groups_admin.input_link"),
        reply_markup=_cancel_keyboard(i18n, lang),
    )


@groups_admin_router.message(AddGroupStates.input_link)
async def group_link_input(message: Message, state: FSMContext, i18n: I18nMiddleware) -> None:
    lang = i18n.get_user_language(message.from_user.id)
    normalized = _normalize_link(message.text or "")
    if not normalized:
        await message.answer(i18n.get_text(lang, "groups_admin.invalid_link"))
        return
    await state.update_data(telegram_link=normalized)

    await state.set_state(AddGroupStates.confirming)
    data = await state.get_data()
    preview = i18n.get_text(
        lang,
        "groups_admin.preview",
        category_name=data.get("category_name", "—"),
        emoji=data.get("emoji", "📌"),
        name_uz=data.get("name_uz", "—"),
        name_ru=data.get("name_ru", "—"),
        name_tr=data.get("name_tr", "—"),
        link=normalized,
    )
    await message.answer(
        preview,
        reply_markup=confirm_keyboard(
            lang=lang, i18n=i18n,
            confirm_callback="grp:confirm",
            cancel_callback="grp:cancel",
        ),
    )


# ============== Skip (faqat emoji uchun) ==============

@groups_admin_router.callback_query(F.data == "grp:skip")
async def group_skip(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    lang = i18n.get_user_language(callback.from_user.id)
    current = await state.get_state()
    await callback.message.edit_reply_markup(reply_markup=None)

    if current == AddGroupStates.input_emoji.state:
        await state.update_data(emoji="📌")
        await state.set_state(AddGroupStates.input_name_uz)
        await callback.message.answer(
            i18n.get_text(lang, "groups_admin.input_name_uz"),
            reply_markup=_cancel_keyboard(i18n, lang),
        )
    elif current == AddCategoryStates.input_emoji.state:
        await state.update_data(emoji="📂")
        await state.set_state(AddCategoryStates.input_name_uz)
        await callback.message.answer(
            i18n.get_text(lang, "groups_admin.category_input_name_uz"),
            reply_markup=_cancel_keyboard(i18n, lang, cancel_cb="grp_cat:cancel"),
        )
    else:
        await callback.answer("⚠️", show_alert=True)
        return

    await callback.answer()


# ============== Cancel (guruh) ==============

@groups_admin_router.callback_query(F.data == "grp:cancel")
async def group_cancel(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    lang = i18n.get_user_language(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(
        i18n.get_text(lang, "groups_admin.cancelled"),
        reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="manager:groups"),
    )
    await callback.answer()


# ============== Confirm — guruhni DBga yozish ==============

@groups_admin_router.callback_query(F.data == "grp:confirm")
async def group_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    lang = i18n.get_user_language(callback.from_user.id)
    data = await state.get_data()

    required = ["name_uz", "name_ru", "name_tr", "telegram_link", "category_id"]
    if not all(data.get(k) for k in required):
        await callback.answer(i18n.get_text(lang, "errors.session_expired"), show_alert=True)
        await state.clear()
        return

    async with get_session() as session:
        group = await group_crud.create(
            session=session,
            name_uz=data["name_uz"],
            name_ru=data["name_ru"],
            name_tr=data["name_tr"],
            telegram_link=data["telegram_link"],
            emoji=data.get("emoji", "📌"),
            category_id=data["category_id"],
        )
        await session.commit()
        group_id = group.id

    logger.info(
        f"Guruh qo'shildi — Manager: {callback.from_user.id}, "
        f"Group: {group_id}, Category: {data['category_id']}, Name: {data['name_uz']}"
    )

    await callback.message.edit_text(
        i18n.get_text(lang, "groups_admin.saved", name=data["name_uz"]),
        reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="manager:groups"),
    )
    await callback.answer()
    await state.clear()


# ============== /cancel komandasi ==============

@groups_admin_router.message(Command("cancel"))
async def cancel_cmd(
    message: Message,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    current = await state.get_state()
    if current is None or not (current.startswith("AddGroupStates:") or current.startswith("AddCategoryStates:")):
        return
    lang = i18n.get_user_language(message.from_user.id)
    await state.clear()
    await message.answer(i18n.get_text(lang, "groups_admin.cancelled"))
