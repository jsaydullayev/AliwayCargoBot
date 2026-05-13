"""
Client: Yukni kuzatish handleri (TZ §6.4)
Cargo ID + clientga tegishli bo'lishi shart
Cargo ID
"""
import logging

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command

from bot.keyboards.inline_kb import navigation_keyboard
from bot.middlewares.i18n_middleware import I18nMiddleware
from bot.utils.notifications import STATUS_KEY_MAP
from database.crud import client_crud, shipment_crud
from database.database import get_session

logger = logging.getLogger(__name__)
track_router = Router()


class TrackStates(StatesGroup):
    waiting_cargo_id = State()


@track_router.callback_query(F.data == "client:track_cargo")
async def track_cargo_start(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Yuk kuzatishni boshlash — Cargo ID so'rash"""
    lang = i18n.get_user_language(callback.from_user.id)
    await state.clear()
    await state.set_state(TrackStates.waiting_cargo_id)

    await callback.message.edit_text(
        i18n.get_text(lang, "track_cargo.request_cargo_id"),
        reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="client:menu"),
    )
    await callback.answer()


@track_router.message(TrackStates.waiting_cargo_id)
async def cargo_id_input(
    message: Message,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Cargo ID qabul qilindi — clientga tegishli ekanini tekshirish"""
    lang = i18n.get_user_language(message.from_user.id)
    cargo_id = (message.text or "").strip()

    if len(cargo_id) != 5 or not cargo_id.isdigit():
        await message.answer(i18n.get_text(lang, "manage_cargo.errors.invalid_cargo_id"))
        return

    back_kb = navigation_keyboard(lang=lang, i18n=i18n, back_callback="client:menu")

    async with get_session() as session:
        # Foydalanuvchining o'z clientini topish (TZ §6.4 — faqat o'z yukini kuzatish)
        client = await client_crud.get_by_telegram_id(session, message.from_user.id)

        if not client:
            await message.answer(i18n.get_text(lang, "errors.client_not_registered"), reply_markup=back_kb)
            await state.clear()
            return

        if not client.cargo_id:
            await message.answer(i18n.get_text(lang, "my_cargo.no_cargo_id"), reply_markup=back_kb)
            await state.clear()
            return

        if client.cargo_id != cargo_id:
            await message.answer(i18n.get_text(lang, "track_cargo.cargo_not_found"), reply_markup=back_kb)
            await state.clear()
            return

        latest = await shipment_crud.get_latest_by_cargo_id(session, cargo_id)

    if not latest:
        await message.answer(i18n.get_text(lang, "my_cargo.no_shipments"), reply_markup=back_kb)
        await state.clear()
        return

    status_text = i18n.get_text(lang, STATUS_KEY_MAP.get(latest.status, ""))

    # Price + currency birga shakllantirish — bo'sh valyutada trailing space bo'lmaydi
    if latest.price:
        price_display = f"{latest.price} {latest.currency or ''}".strip()
    else:
        price_display = "—"

    info_text = i18n.get_text(
        lang,
        "track_cargo.cargo_info",
        cargo_id=client.cargo_id,
        description=latest.description or "—",
        weight=f"{latest.weight_kg} kg" if latest.weight_kg else "—",
        cargo_weight=f"{latest.cargo_weight_kg} kg" if latest.cargo_weight_kg else "—",
        price=price_display,
        status=status_text,
        notes=latest.notes or "—",
        created_at=latest.created_at.strftime("%d.%m.%Y %H:%M") if latest.created_at else "—",
    )

    buttons = []
    if latest.photo_file_id:
        buttons.append([
            InlineKeyboardButton(
                text=i18n.get_text(lang, "track_cargo.view_photo"),
                callback_data=f"track:photo:{latest.id}",
            ),
        ])
    buttons.append([
        InlineKeyboardButton(
            text=i18n.get_text(lang, "buttons.back"),
            callback_data="client:menu",
        ),
    ])

    await message.answer(info_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await state.clear()


@track_router.callback_query(F.data.startswith("track:photo:"))
async def view_photo(
    callback: CallbackQuery,
    i18n: I18nMiddleware,
    bot: Bot,
) -> None:
    """Yuk rasmini ko'rsatish"""
    lang = i18n.get_user_language(callback.from_user.id)

    try:
        shipment_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("⚠️", show_alert=True)
        return

    async with get_session() as session:
        shipment = await shipment_crud.get_by_id(session, shipment_id)

    if not shipment or not shipment.photo_file_id:
        await callback.answer(i18n.get_text(lang, "track_cargo.cargo_not_found"))
        return

    # Telegram_id tegishlilik tekshiruvi (xavfsizlik)
    if shipment.client.telegram_id != callback.from_user.id:
        await callback.answer(i18n.get_text(lang, "track_cargo.no_access"), show_alert=True)
        return

    try:
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=shipment.photo_file_id,
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Rasm yuborib bo'lmadi (shipment {shipment_id}): {e}")
        await callback.answer(i18n.get_text(lang, "errors.unknown_error"), show_alert=True)


@track_router.message(Command("cancel"))
async def cancel_track(
    message: Message,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    current = await state.get_state()
    if current is None or not current.startswith("TrackStates:"):
        return
    lang = i18n.get_user_language(message.from_user.id)
    await state.clear()
    await message.answer(i18n.get_text(lang, "manage_cargo.cancelled"))
