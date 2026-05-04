"""
Client onboarding (TZ §6.2)
/start → til tanlash → telefon raqam → asosiy menyu
"""
import logging

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.keyboards.inline_kb import language_selection_keyboard
from bot.middlewares.i18n_middleware import I18nMiddleware
from config import settings
from database.crud import client_crud, company_info_crud
from database.database import get_session

logger = logging.getLogger(__name__)
onboarding_router = Router()


class OnboardingStates(StatesGroup):
    selecting_language = State()
    waiting_contact = State()


def _contact_request_keyboard(i18n: I18nMiddleware, lang: str) -> ReplyKeyboardMarkup:
    button_text = i18n.get_text(lang, "buttons.share_phone")
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=button_text, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
        is_persistent=False,
    )


def client_main_keyboard(i18n: I18nMiddleware, lang: str) -> InlineKeyboardMarkup:
    """Client asosiy menyu klaviaturasi — 2 ustunli (TZ §6.1)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=i18n.get_text(lang, "client_menu.buttons.my_cargo"),
                callback_data="client:my_cargo",
            ),
            InlineKeyboardButton(
                text=i18n.get_text(lang, "client_menu.buttons.track_cargo"),
                callback_data="client:track_cargo",
            ),
        ],
        [
            InlineKeyboardButton(
                text=i18n.get_text(lang, "client_menu.buttons.groups"),
                callback_data="client:groups",
            ),
            InlineKeyboardButton(
                text=i18n.get_text(lang, "client_menu.buttons.contacts"),
                callback_data="client:contacts",
            ),
        ],
        [
            InlineKeyboardButton(
                text=i18n.get_text(lang, "client_menu.buttons.settings"),
                callback_data="client:settings",
            ),
            InlineKeyboardButton(
                text=i18n.get_text(lang, "client_menu.buttons.change_language"),
                callback_data="client:change_lang",
            ),
        ],
    ])


async def show_main_menu(
    message: Message,
    i18n: I18nMiddleware,
    lang: str,
    edit: bool = False,
) -> None:
    """Asosiy menyuni ko'rsatish"""
    title = i18n.get_text(lang, "client_menu.title")
    tagline = i18n.get_text(lang, "client_menu.tagline")
    footer = i18n.get_text(lang, "client_menu.footer")

    text = f"{title}\n\n{tagline}"

    async with get_session() as session:
        company_info = await company_info_crud.get(session)

    if company_info:
        cn_address = getattr(company_info, "address_cn", "") or ""
        cn_phones = getattr(company_info, "phone_numbers_cn", []) or []
        if cn_address or cn_phones:
            china_label = i18n.get_text(lang, "contacts.china_office")
            text += f"\n\n━━━━━━━━━━━━━━━━━━━━\n{china_label}"
            if cn_address:
                text += f"\n📍 {cn_address}"
            if cn_phones:
                text += f"\n📱 {', '.join(cn_phones)}"
            text += "\n━━━━━━━━━━━━━━━━━━━━"

    text += f"\n\n{footer}"

    keyboard = client_main_keyboard(i18n, lang)

    if edit:
        try:
            await message.edit_text(text, reply_markup=keyboard)
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=keyboard)


@onboarding_router.message(CommandStart(), F.from_user.id.not_in(settings.MANAGER_IDS))
async def cmd_start(
    message: Message,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """`/start` — client uchun"""
    await state.clear()
    user_id = message.from_user.id

    async with get_session() as session:
        existing = await client_crud.get_by_telegram_id(session, user_id)

    if existing:
        lang = existing.language or "uz"
        i18n._cache[user_id] = lang
        await message.answer(i18n.get_text(lang, "welcome"), reply_markup=ReplyKeyboardRemove())
        await show_main_menu(message, i18n, lang)
        return

    # Yangi foydalanuvchi → til tanlash
    await state.set_state(OnboardingStates.selecting_language)
    await message.answer(
        i18n.get_text("uz", "welcome") + "\n\n" + i18n.get_text("uz", "select_language"),
        reply_markup=language_selection_keyboard(),
    )


@onboarding_router.callback_query(
    OnboardingStates.selecting_language,
    F.data.startswith("lang:"),
)
async def language_selected(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Til tanlandi (yangi foydalanuvchi)"""
    lang = callback.data.split(":")[1]
    if lang not in ("uz", "ru", "tr"):
        await callback.answer("⚠️", show_alert=True)
        return

    await state.update_data(lang=lang)
    i18n._cache[callback.from_user.id] = lang

    await callback.message.edit_text(i18n.get_text(lang, "language_selected"))

    await state.set_state(OnboardingStates.waiting_contact)
    await callback.message.answer(
        i18n.get_text(lang, "request_contact"),
        reply_markup=_contact_request_keyboard(i18n, lang),
    )
    await callback.answer()


@onboarding_router.message(OnboardingStates.waiting_contact, F.contact)
async def contact_received(
    message: Message,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Telefon raqam qabul qilindi"""
    data = await state.get_data()
    lang = data.get("lang", "uz")

    phone_number = message.contact.phone_number or ""
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"

    user_id = message.from_user.id
    full_name = message.from_user.full_name

    async with get_session() as session:
        existing = await client_crud.get_by_phone(session, phone_number)

        if existing:
            await client_crud.link_telegram(session, phone_number, user_id, language=lang)
            existing.full_name = full_name or existing.full_name
            await session.commit()
            client = existing
        else:
            client = await client_crud.create(
                session=session,
                phone_number=phone_number,
                cargo_id=None,
                created_by=user_id,
                telegram_id=user_id,
                full_name=full_name,
                language=lang,
            )
            await session.commit()

    i18n._cache[user_id] = lang
    await state.clear()

    await message.answer(
        i18n.get_text(lang, "contact_received"),
        reply_markup=ReplyKeyboardRemove(),
    )
    await show_main_menu(message, i18n, lang)


@onboarding_router.message(OnboardingStates.waiting_contact)
async def invalid_contact(
    message: Message,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await message.answer(
        i18n.get_text(lang, "errors.invalid_phone"),
        reply_markup=_contact_request_keyboard(i18n, lang),
    )


@onboarding_router.callback_query(F.data == "client:menu")
async def back_to_menu(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nMiddleware,
) -> None:
    """Asosiy menyuga qaytish"""
    await state.clear()
    lang = i18n.get_user_language(callback.from_user.id)
    await show_main_menu(callback.message, i18n, lang, edit=True)
    await callback.answer()
