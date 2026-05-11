"""
Client: Mening Cargo ID im (TZ §6.3)
"""
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards.inline_kb import navigation_keyboard
from bot.middlewares.i18n_middleware import I18nMiddleware
from bot.utils.notifications import STATUS_KEY_MAP
from database.crud import client_crud, shipment_crud
from database.database import get_session

logger = logging.getLogger(__name__)
my_cargo_router = Router()


@my_cargo_router.callback_query(F.data == "client:my_cargo")
async def show_my_cargo(
    callback: CallbackQuery,
    i18n: I18nMiddleware,
) -> None:
    """Cargo ID va yuklarni chiroyli ko'rinishda ko'rsatish"""
    lang = i18n.get_user_language(callback.from_user.id)
    user_id = callback.from_user.id

    async with get_session() as session:
        client = await client_crud.get_by_telegram_id(session, user_id)

        if not client:
            await callback.message.edit_text(
                f"⚠️ {i18n.get_text(lang, 'errors.client_not_registered')}",
                reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="client:menu"),
            )
            await callback.answer()
            return

        if not client.cargo_id:
            text = (
                f"{i18n.get_text(lang, 'my_cargo.title')}\n\n"
                f"{i18n.get_text(lang, 'my_cargo.no_cargo_id')}\n\n"
                f"{i18n.get_text(lang, 'my_cargo.contact_admin')}"
            )
            await callback.message.edit_text(
                text,
                reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="client:menu"),
            )
            await callback.answer()
            return

        shipments = await shipment_crud.get_by_client(session, client.id, limit=50)

    text_parts = [
        i18n.get_text(lang, "my_cargo.title"),
        "",
        i18n.get_text(lang, "my_cargo.your_cargo_id", cargo_id=client.cargo_id),
        "",
    ]

    if not shipments:
        text_parts.append(i18n.get_text(lang, "my_cargo.no_shipments"))
    else:
        text_parts.append(i18n.get_text(lang, "my_cargo.your_shipments"))
        text_parts.append("")
        for idx, ship in enumerate(shipments, start=1):
            status_text = i18n.get_text(lang, STATUS_KEY_MAP.get(ship.status, ""))
            created_at = ship.created_at.strftime("%d.%m.%Y") if ship.created_at else "—"
            description = ship.description or "—"
            item = i18n.get_text(
                lang,
                "my_cargo.shipment_item",
                idx=idx,
                description=description,
                status=status_text,
                date=created_at,
            )
            text_parts.append(item)
            text_parts.append("")

    text = "\n".join(text_parts).rstrip()

    await callback.message.edit_text(
        text,
        reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="client:menu"),
    )
    await callback.answer()
