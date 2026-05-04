"""
Status yangilash handleri (TZ §5.4)
Cargo ID → joriy status ko'rsatish → yangi status tanlash → notification
"""
import logging

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.keyboards.inline_kb import navigation_keyboard
from bot.middlewares.i18n_middleware import I18nMiddleware
from bot.utils.notifications import send_status_notification, STATUS_KEY_MAP
from database.crud import shipment_crud
from database.database import get_session
from database.models import CargoStatus

logger = logging.getLogger(__name__)
update_status_router = Router()


class UpdateStatusStates(StatesGroup):
    """Status yangilash FSM"""
    waiting_cargo_id = State()
    selecting_status = State()


def _status_keyboard(i18n: I18nMiddleware, lang: str, current: CargoStatus) -> InlineKeyboardMarkup:
    """5 ta status tugma + back"""
    rows = []
    statuses = [
        CargoStatus.PENDING,
        CargoStatus.IN_TRANSIT,
        CargoStatus.ARRIVED,
        CargoStatus.READY,
        CargoStatus.DELIVERED,
    ]

    pair = []
    for status in statuses:
        is_current = status == current
        prefix = "🔵 " if is_current else ""
        text = i18n.get_text(lang, STATUS_KEY_MAP[status])
        pair.append(InlineKeyboardButton(
            text=f"{prefix}{text}",
            callback_data=f"set_status:{status.value}",
        ))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)

    rows.append([
        InlineKeyboardButton(
            text=i18n.get_text(lang, "buttons.back"),
            callback_data="manager:menu",
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


@update_status_router.callback_query(F.data == "manager:update_status")
async def update_status_start(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Status yangilashni boshlash"""
    lang = i18n.get_user_language(callback.from_user.id)
    await state.clear()
    await state.set_state(UpdateStatusStates.waiting_cargo_id)

    await callback.message.edit_text(
        i18n.get_text(lang, "update_status.request_cargo_id"),
        reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="manager:menu"),
    )
    await callback.answer()


@update_status_router.message(UpdateStatusStates.waiting_cargo_id)
async def cargo_id_input(
    message: Message,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Cargo ID qabul qilindi"""
    lang = i18n.get_user_language(message.from_user.id)
    cargo_id = (message.text or "").strip()

    if len(cargo_id) != 5 or not cargo_id.isdigit():
        await message.answer(i18n.get_text(lang, "manage_cargo.errors.invalid_cargo_id"))
        return

    async with get_session() as session:
        latest = await shipment_crud.get_latest_by_cargo_id(session, cargo_id)

    if not latest:
        await message.answer(i18n.get_text(lang, "manage_cargo.cargo_not_found"))
        return

    client = latest.client
    current_status_text = i18n.get_text(lang, STATUS_KEY_MAP.get(latest.status, ""))

    info_text = i18n.get_text(
        lang,
        "update_status.shipment_info",
        name=client.full_name or "—",
        cargo_id=client.cargo_id,
        description=latest.description or "—",
        status=current_status_text,
    )

    await state.update_data(
        shipment_id=latest.id,
        cargo_id=cargo_id,
        current_status=latest.status.value,
    )
    await state.set_state(UpdateStatusStates.selecting_status)

    await message.answer(
        f"{info_text}\n\n{i18n.get_text(lang, 'update_status.select_new_status')}",
        reply_markup=_status_keyboard(i18n, lang, latest.status),
    )


@update_status_router.callback_query(
    UpdateStatusStates.selecting_status,
    F.data.startswith("set_status:"),
)
async def status_selected(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
    bot: Bot,
) -> None:
    """Yangi status tanlandi"""
    lang = i18n.get_user_language(callback.from_user.id)
    data = await state.get_data()

    new_status_str = callback.data.split(":")[1]
    current_status_str = data.get("current_status")
    shipment_id = data.get("shipment_id")

    try:
        new_status = CargoStatus(new_status_str)
    except ValueError:
        await callback.answer("⚠️", show_alert=True)
        return

    if new_status_str == current_status_str:
        await callback.answer(i18n.get_text(lang, "update_status.same_status"), show_alert=True)
        return

    if not shipment_id:
        await callback.answer(i18n.get_text(lang, "errors.session_expired"), show_alert=True)
        await state.clear()
        return

    client = None
    async with get_session() as session:
        updated = await shipment_crud.update_status(session, shipment_id, new_status)
        await session.commit()
        if updated:
            client = updated.client  # eager-loaded by update_status

    notification_sent = False
    if updated and client:
        notification_sent = await send_status_notification(
            bot=bot,
            client=client,
            shipment=updated,
            i18n=i18n,
        )

    new_status_text = i18n.get_text(lang, STATUS_KEY_MAP[new_status])
    result_text = i18n.get_text(lang, "update_status.updated", status=new_status_text)
    if notification_sent:
        result_text += f"\n\n{i18n.get_text(lang, 'create_cargo.notification_sent')}"

    logger.info(
        f"Status yangilandi — Manager: {callback.from_user.id}, "
        f"Shipment: {shipment_id}, Status: {new_status.value}"
    )

    await callback.message.edit_text(
        result_text,
        reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="manager:menu"),
    )
    await callback.answer()
    await state.clear()
