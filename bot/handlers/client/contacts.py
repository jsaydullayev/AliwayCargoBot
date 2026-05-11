"""
Client: Bog'lanish — kompaniya ma'lumotlari (TZ §6.6)
"""
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards.inline_kb import navigation_keyboard
from bot.middlewares.i18n_middleware import I18nMiddleware
from database.crud import company_info_crud
from database.database import get_session

logger = logging.getLogger(__name__)
contacts_router = Router()


@contacts_router.callback_query(F.data == "client:contacts")
async def show_contacts(
    callback: CallbackQuery,
    i18n: I18nMiddleware,
) -> None:
    """Kompaniya kontakt ma'lumotlarini chiroyli ko'rsatish"""
    lang = i18n.get_user_language(callback.from_user.id)

    async with get_session() as session:
        info = await company_info_crud.get(session)

    title = i18n.get_text(lang, "contacts.title")
    parts = [title, ""]

    if info:
        # Xitoy ofisi (barch tillarda bir xil ma'lumotlar)
        cn_address = getattr(info, "address_cn", "") or ""
        cn_phones = getattr(info, "phone_numbers_cn", []) or []
        telegram_account = info.telegram_account or ""

        if cn_address:
            parts.append(f"{i18n.get_text(lang, 'contacts.address')}")
            parts.append(f"   {cn_address}")
            parts.append("")

        if cn_phones:
            parts.append(f"{i18n.get_text(lang, 'contacts.phones')}")
            for phone in cn_phones:
                parts.append(f"   {phone}")
            parts.append("")

        if telegram_account:
            parts.append(f"{i18n.get_text(lang, 'contacts.telegram')}")
            parts.append(f"   @{telegram_account}")
            parts.append("")
    else:
        parts.append(i18n.get_text(lang, "contacts.address_not_specified"))

    text = "\n".join(parts).rstrip()

    await callback.message.edit_text(
        text,
        reply_markup=navigation_keyboard(lang=lang, i18n=i18n, back_callback="client:menu"),
    )
    await callback.answer()
