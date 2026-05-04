"""
Excel eksport handleri (TZ §5.6)
"""
import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.keyboards.inline_kb import navigation_keyboard
from bot.middlewares.i18n_middleware import I18nMiddleware
from bot.utils.excel_export import generate_excel_file
from bot.utils.notifications import STATUS_KEY_MAP
from database.crud import shipment_crud
from database.database import get_session
from database.models import CargoStatus

logger = logging.getLogger(__name__)
export_router = Router()


class ExportStates(StatesGroup):
    selecting_filter = State()


def _export_filter_keyboard(i18n: I18nMiddleware, lang: str) -> InlineKeyboardMarkup:
    statuses = [
        CargoStatus.PENDING,
        CargoStatus.IN_TRANSIT,
        CargoStatus.ARRIVED,
        CargoStatus.READY,
        CargoStatus.DELIVERED,
    ]
    rows = [
        [
            InlineKeyboardButton(
                text=i18n.get_text(lang, "view_cargos.all_cargos"),
                callback_data="export:all",
            ),
        ],
    ]
    pair = []
    for s in statuses:
        pair.append(InlineKeyboardButton(
            text=i18n.get_text(lang, STATUS_KEY_MAP[s]),
            callback_data=f"export:status:{s.value}",
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


@export_router.callback_query(F.data == "manager:export")
async def export_menu(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Eksport menyusi"""
    lang = i18n.get_user_language(callback.from_user.id)
    await state.clear()
    await state.set_state(ExportStates.selecting_filter)

    await callback.message.edit_text(
        f"📥 <b>{i18n.get_text(lang, 'export.title')}</b>\n\n"
        f"{i18n.get_text(lang, 'export.select_filter')}",
        reply_markup=_export_filter_keyboard(i18n, lang),
    )
    await callback.answer()


@export_router.callback_query(F.data == "export:all")
async def export_all(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    await _do_export(callback, i18n, state, status_filter=None)


@export_router.callback_query(F.data.startswith("export:status:"))
async def export_by_status(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    try:
        status_value = callback.data.split(":")[2]
        status = CargoStatus(status_value)
    except (IndexError, ValueError):
        await callback.answer("⚠️", show_alert=True)
        return

    await _do_export(callback, i18n, state, status_filter=status)


async def _do_export(
    callback: CallbackQuery,
    i18n: I18nMiddleware,
    state: FSMContext,
    status_filter: CargoStatus | None,
) -> None:
    """Eksportni amalga oshirish"""
    lang = i18n.get_user_language(callback.from_user.id)

    await callback.message.edit_text(
        i18n.get_text(lang, "export.generating"),
    )

    try:
        async with get_session() as session:
            shipments = await shipment_crud.get_all_for_export(session, active_only=False)
            if status_filter:
                shipments = [s for s in shipments if s[8] == status_filter]

        if not shipments:
            await callback.message.edit_text(
                i18n.get_text(lang, "export.no_data"),
                reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="manager:menu"),
            )
            await state.clear()
            await callback.answer()
            return

        file = generate_excel_file(shipments)

        await callback.message.answer_document(
            document=file,
            caption=f"✅ {i18n.get_text(lang, 'export.done')}",
        )
        await callback.message.edit_text(
            f"✅ {i18n.get_text(lang, 'export.done')}",
            reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="manager:menu"),
        )
        logger.info(f"Excel eksport — Manager: {callback.from_user.id}, Rows: {len(shipments)}")

    except Exception as e:
        logger.error(f"Eksport xatosi: {e}", exc_info=True)
        await callback.message.edit_text(
            i18n.get_text(lang, "errors.unknown_error"),
            reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="manager:menu"),
        )

    await state.clear()
    await callback.answer()
