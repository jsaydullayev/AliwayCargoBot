"""
Yangi Cargo ID yaratish handleri (TZ §5.2)
Telefon raqam orqali mijoz uchun yangi yoki mavjud Cargo ID
"""
import logging
import re

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.keyboards.inline_kb import yes_no_keyboard, navigation_keyboard
from bot.middlewares.i18n_middleware import I18nMiddleware
from bot.utils.cargo_id_gen import cargo_id_generator
from bot.utils.notifications import send_cargo_id_notification
from database.crud import client_crud
from database.database import get_session

logger = logging.getLogger(__name__)
create_cargo_router = Router()


class CreateCargoStates(StatesGroup):
    """Cargo ID yaratish FSM state lari"""
    waiting_phone = State()
    choosing_action = State()   # mavjud cargo_id egasi uchun: use / new / cancel
    confirming_update = State()
    confirming_new = State()


def _existing_cargo_choice_keyboard(i18n: I18nMiddleware, lang: str) -> InlineKeyboardMarkup:
    """TZ §5.2 HOLAT B — 3 ta tugma: mavjud / yangi / bekor"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=i18n.get_text(lang, "create_cargo.use_existing"),
                callback_data="create_cargo:use_existing",
            ),
        ],
        [
            InlineKeyboardButton(
                text=i18n.get_text(lang, "create_cargo.create_new"),
                callback_data="create_cargo:create_new",
            ),
        ],
        [
            InlineKeyboardButton(
                text=i18n.get_text(lang, "buttons.cancel"),
                callback_data="create_cargo:cancel",
            ),
        ],
    ])


def validate_phone_number(phone: str) -> tuple[bool, str]:
    """
    Telefon raqamni validatsiya qilish va normalizatsiya

    Qabul qilinadigan formatlar:
    - +998901234567, 998901234567, 901234567 (O'zbek)
    - +905551234567, +75551234567 va boshqa xalqaro

    Returns:
        (is_valid, normalized_phone)
    """
    if not phone:
        return False, ""

    cleaned = re.sub(r"[\s\-()]", "", phone.strip())
    digits = re.sub(r"[^\d]", "", cleaned)

    if not digits:
        return False, ""

    if cleaned.startswith("+"):
        if 9 <= len(digits) <= 15:
            return True, f"+{digits}"
        return False, ""

    if len(digits) == 9 and digits[0] in "9":
        return True, f"+998{digits}"

    if 9 <= len(digits) <= 15:
        return True, f"+{digits}"

    return False, ""


@create_cargo_router.callback_query(F.data == "manager:create_cargo")
async def create_cargo_start(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Cargo ID yaratishni boshlash — telefon raqam so'rash"""
    lang = i18n.get_user_language(callback.from_user.id)

    await state.clear()
    await state.set_state(CreateCargoStates.waiting_phone)

    await callback.message.edit_text(
        i18n.get_text(lang, "create_cargo.request_phone"),
        reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="manager:menu"),
    )
    await callback.answer()


@create_cargo_router.message(CreateCargoStates.waiting_phone)
async def phone_received(
    message: Message,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Telefon raqam qabul qilindi — DB orqali qidirish"""
    lang = i18n.get_user_language(message.from_user.id)

    is_valid, phone = validate_phone_number(message.text or "")

    if not is_valid:
        await message.answer(i18n.get_text(lang, "create_cargo.phone_format"))
        return

    async with get_session() as session:
        existing_client = await client_crud.get_by_phone(session, phone)

    if existing_client:
        await _handle_existing_client(message, state, i18n, lang, existing_client, phone)
    else:
        await _confirm_new_client(message, state, i18n, lang, phone)


async def _handle_existing_client(
    message: Message,
    state: FSMContext,
    i18n: I18nMiddleware,
    lang: str,
    client,
    phone: str,
) -> None:
    """Mavjud client topildi — TZ §5.2 HOLAT B"""
    created_at_str = client.created_at.strftime("%d.%m.%Y") if client.created_at else "—"

    if client.cargo_id:
        info_text = (
            f"⚠️ <b>{i18n.get_text(lang, 'create_cargo.existing_cargo')}</b>\n\n"
            f"👤 <b>{i18n.get_text(lang, 'create_cargo.client_info.name')}</b>: "
            f"{client.full_name or '—'}\n"
            f"📞 <b>{i18n.get_text(lang, 'create_cargo.client_info.phone')}</b>: {phone}\n"
            f"🆔 <b>{i18n.get_text(lang, 'create_cargo.client_info.cargo_id')}</b>: "
            f"<code>{client.cargo_id}</code>\n"
            f"📅 <b>{i18n.get_text(lang, 'create_cargo.client_info.created_at')}</b>: "
            f"{created_at_str}\n\n"
            f"{i18n.get_text(lang, 'create_cargo.choose_action')}"
        )

        await state.set_state(CreateCargoStates.choosing_action)
        await state.update_data(client_id=client.id, phone=phone, old_cargo_id=client.cargo_id)

        await message.answer(
            info_text,
            reply_markup=_existing_cargo_choice_keyboard(i18n, lang),
        )
    else:
        info_text = (
            f"✅ <b>{i18n.get_text(lang, 'create_cargo.client_found')}</b>\n\n"
            f"👤 <b>{client.full_name or '—'}</b>\n"
            f"📞 <b>{phone}</b>\n\n"
            f"⚠️ {i18n.get_text(lang, 'create_cargo.no_cargo_id')}\n\n"
            f"❓ {i18n.get_text(lang, 'create_cargo.confirm_client')}"
        )

        await state.set_state(CreateCargoStates.confirming_new)
        await state.update_data(client_id=client.id, phone=phone)

        await message.answer(
            info_text,
            reply_markup=yes_no_keyboard(
                lang=lang,
                i18n=i18n,
                yes_callback="create_cargo:new_yes",
                no_callback="create_cargo:cancel",
            ),
        )


async def _confirm_new_client(
    message: Message,
    state: FSMContext,
    i18n: I18nMiddleware,
    lang: str,
    phone: str,
) -> None:
    """Yangi client uchun tasdiqlash — TZ §5.2 HOLAT A"""
    info_text = (
        f"📞 <b>Telefon</b>: {phone}\n\n"
        f"⚠️ {i18n.get_text(lang, 'create_cargo.client_not_found')}"
    )

    await state.set_state(CreateCargoStates.confirming_new)
    await state.update_data(client_id=None, phone=phone)

    await message.answer(
        info_text,
        reply_markup=yes_no_keyboard(
            lang=lang,
            i18n=i18n,
            yes_callback="create_cargo:new_yes",
            no_callback="create_cargo:cancel",
        ),
    )


@create_cargo_router.callback_query(F.data == "create_cargo:use_existing")
async def use_existing_id(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Mavjud Cargo ID dan foydalanish — TZ §5.2 HOLAT B birinchi tugma"""
    lang = i18n.get_user_language(callback.from_user.id)
    data = await state.get_data()
    old_cargo_id = data.get("old_cargo_id")

    if not old_cargo_id:
        await callback.answer(i18n.get_text(lang, "errors.session_expired"), show_alert=True)
        await state.clear()
        return

    await callback.message.edit_text(
        i18n.get_text(lang, "create_cargo.existing_used", cargo_id=old_cargo_id),
        reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="manager:menu"),
    )
    await callback.answer()
    await state.clear()


@create_cargo_router.callback_query(F.data == "create_cargo:create_new")
async def create_new_id_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Yangi ID yaratishni tasdiqlash bosqichi — TZ §5.2 HOLAT B ikkinchi tugma"""
    lang = i18n.get_user_language(callback.from_user.id)
    data = await state.get_data()
    old_cargo_id = data.get("old_cargo_id")

    if not old_cargo_id:
        await callback.answer(i18n.get_text(lang, "errors.session_expired"), show_alert=True)
        await state.clear()
        return

    await state.set_state(CreateCargoStates.confirming_update)
    await callback.message.edit_text(
        i18n.get_text(lang, "create_cargo.new_cargo_confirm", old_id=old_cargo_id),
        reply_markup=yes_no_keyboard(
            lang=lang,
            i18n=i18n,
            yes_callback="create_cargo:update_yes",
            no_callback="create_cargo:cancel",
        ),
    )
    await callback.answer()


@create_cargo_router.callback_query(F.data == "create_cargo:update_yes")
async def update_existing_id(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
    bot: Bot,
) -> None:
    """Mavjud clientga yangi Cargo ID biriktirish"""
    lang = i18n.get_user_language(callback.from_user.id)
    data = await state.get_data()
    client_id = data.get("client_id")
    phone = data.get("phone", "")
    old_cargo_id = data.get("old_cargo_id", "")

    if not client_id:
        await callback.answer(i18n.get_text(lang, "errors.session_expired"), show_alert=True)
        await state.clear()
        return

    notification_sent = False
    async with get_session() as session:
        new_cargo_id = await cargo_id_generator.generate_unique_id(session)
        client = await client_crud.update_cargo_id(session, client_id, new_cargo_id)
        await session.commit()

        if client and client.telegram_id:
            notification_sent = await send_cargo_id_notification(
                bot=bot,
                client=client,
                new_cargo_id=new_cargo_id,
                i18n=i18n,
                old_cargo_id=old_cargo_id,
            )

    result_text = (
        f"{i18n.get_text(lang, 'create_cargo.cargo_updated', old_id=old_cargo_id, new_id=new_cargo_id)}\n\n"
        f"👤 <b>{client.full_name or '—'}</b>\n"
        f"📞 <b>{phone}</b>\n"
    )
    if notification_sent:
        result_text += f"\n{i18n.get_text(lang, 'create_cargo.notification_sent')}"

    await callback.message.edit_text(
        result_text,
        reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="manager:menu"),
    )
    await callback.answer()
    await state.clear()


@create_cargo_router.callback_query(F.data == "create_cargo:new_yes")
async def confirm_new_id(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
    bot: Bot,
) -> None:
    """Yangi ID yaratish tasdiqlandi"""
    lang = i18n.get_user_language(callback.from_user.id)
    data = await state.get_data()
    client_id = data.get("client_id")
    phone = data.get("phone", "")

    if not phone:
        await callback.answer(i18n.get_text(lang, "errors.session_expired"), show_alert=True)
        await state.clear()
        return

    notification_sent = False
    async with get_session() as session:
        new_cargo_id = await cargo_id_generator.generate_unique_id(session)

        if client_id:
            client = await client_crud.update_cargo_id(session, client_id, new_cargo_id)
        else:
            client = await client_crud.create(
                session=session,
                phone_number=phone,
                cargo_id=new_cargo_id,
                created_by=callback.from_user.id,
                telegram_id=None,
                full_name=None,
                language=lang,
            )

        await session.commit()

        if client and client.telegram_id:
            notification_sent = await send_cargo_id_notification(
                bot=bot,
                client=client,
                new_cargo_id=new_cargo_id,
                i18n=i18n,
            )

    result_text = i18n.get_text(
        lang,
        "create_cargo.client_added",
        phone=phone,
        cargo_id=new_cargo_id,
    )
    if notification_sent:
        result_text += f"\n\n{i18n.get_text(lang, 'create_cargo.notification_sent')}"

    await callback.message.edit_text(
        result_text,
        reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="manager:menu"),
    )
    await callback.answer()
    await state.clear()


@create_cargo_router.callback_query(F.data == "create_cargo:cancel")
async def cancel_create_cargo(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Cargo ID yaratishni bekor qilish"""
    lang = i18n.get_user_language(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(
        i18n.get_text(lang, "manage_cargo.cancelled"),
        reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="manager:menu"),
    )
    await callback.answer()
