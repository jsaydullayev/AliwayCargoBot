"""
Inline klaviatura generatorlari — faqat haqiqatda ishlatiladiganlar
"""
from typing import Any

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def _get_text(i18n: Any, lang: str, key: str, **kwargs) -> str:
    """Tarjima — i18n bo'lsa undan, aks holda fallback"""
    if i18n is not None and hasattr(i18n, "get_text"):
        return i18n.get_text(lang, key, **kwargs)
    return key


# === Til tanlash (onboarding va admin change_lang uchun) ===
def language_selection_keyboard() -> InlineKeyboardMarkup:
    """Til tanlash — `lang:uz/ru/tr` callback"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang:uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="🇹🇷 Türkçe", callback_data="lang:tr"),
        ],
    ])


# === Valyuta tanlash (manage_cargo flow) ===
def currency_selection_keyboard(
    lang: str = "uz",
    i18n: Any = None,
) -> InlineKeyboardMarkup:
    """USD / UZS / Skip — `currency:USD/UZS/skip`"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_get_text(i18n, lang, "currencies.usd"),
                callback_data="currency:USD",
            ),
            InlineKeyboardButton(
                text=_get_text(i18n, lang, "currencies.uzs"),
                callback_data="currency:UZS",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_get_text(i18n, lang, "buttons.skip"),
                callback_data="currency:skip",
            ),
        ],
    ])


# === Tasdiq / Bekor (preview, confirmation) ===
def confirm_keyboard(
    lang: str = "uz",
    i18n: Any = None,
    confirm_callback: str = "confirm:yes",
    cancel_callback: str = "cancel:no",
) -> InlineKeyboardMarkup:
    """✅ Tasdiqlash / ❌ Bekor qilish"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_get_text(i18n, lang, "buttons.confirm"),
                callback_data=confirm_callback,
            ),
            InlineKeyboardButton(
                text=_get_text(i18n, lang, "buttons.cancel"),
                callback_data=cancel_callback,
            ),
        ],
    ])


# === Ha / Yo'q (create_cargo confirm) ===
def yes_no_keyboard(
    lang: str = "uz",
    i18n: Any = None,
    yes_callback: str = "yes",
    no_callback: str = "no",
) -> InlineKeyboardMarkup:
    """✅ Ha / ❌ Yo'q"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_get_text(i18n, lang, "buttons.yes"),
                callback_data=yes_callback,
            ),
            InlineKeyboardButton(
                text=_get_text(i18n, lang, "buttons.no"),
                callback_data=no_callback,
            ),
        ],
    ])


# === Orqaga qaytish ===
def navigation_keyboard(
    lang: str = "uz",
    i18n: Any = None,
    back_callback: str = "back",
) -> InlineKeyboardMarkup:
    """◀️ Orqaga"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_get_text(i18n, lang, "buttons.back"),
                callback_data=back_callback,
            ),
        ],
    ])
