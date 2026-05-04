"""
Manager klaviaturalari - Reply keyboards
"""
from typing import Optional

from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def manager_menu_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """
    Manager asosiy menyusi (lokalizatsiyalangan)

    Args:
        lang: Til kodi (uz, ru, tr)

    Returns:
        ReplyKeyboardMarkup
    """
    # Turga ko'ra matnlar
    buttons_map = {
        "uz": {
            "create_cargo": "➕ Yangi Cargo ID yaratish",
            "manage_cargo": "📦 Yuk biriktirish",
            "update_status": "🔄 Status yangilash",
            "view_cargos": "🔍 Yuklarni ko'rish",
            "export": "📥 Excel eksport"
        },
        "ru": {
            "create_cargo": "➕ Создать новый Cargo ID",
            "manage_cargo": "📦 Добавить груз",
            "update_status": "🔄 Обновить статус",
            "view_cargos": "🔍 Просмотреть грузы",
            "export": "📥 Экспорт в Excel"
        },
        "tr": {
            "create_cargo": "➕ Yeni Cargo ID oluştur",
            "manage_cargo": "📦 Yük ekle",
            "update_status": "🔄 Durumu güncelle",
            "view_cargos": "🔍 Yükleri görüntüle",
            "export": "📥 Excel'e aktar"
        }
    }

    # Tanlangan til uchun tugmalar
    buttons = buttons_map.get(lang, buttons_map["uz"])

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=buttons["create_cargo"]),
            ],
            [
                KeyboardButton(text=buttons["manage_cargo"]),
            ],
            [
                KeyboardButton(text=buttons["update_status"]),
            ],
            [
                KeyboardButton(text=buttons["view_cargos"]),
            ],
            [
                KeyboardButton(text=buttons["export"]),
            ]
        ],
        resize_keyboard=True,
        is_persistent=False,
    )


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    """Telefon raqam so'rash keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        is_persistent=False,
        one_time_keyboard=True,
    )


def cargo_id_request_keyboard() -> ReplyKeyboardMarkup:
    """Cargo ID so'rash keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        is_persistent=False,
        one_time_keyboard=True,
    )


def shipment_fields_keyboard(skip_fields: list = None) -> ReplyKeyboardMarkup:
    """
    Yuk maydonlari keyboardi

    Args:
        skip_fields: O'tkazib yuborilgan maydonlar ro'yxati
    """
    skip_fields = skip_fields or []

    buttons = []

    # Yuk nimaligi (majburiy) - skip tugmasi
    if "description" not in skip_fields:
        buttons.append([KeyboardButton(text="⏭️ O'tkazib yuborish")])

    # Narx kiritilgan bo'lsa valyuta tanlash
    if "currency" not in skip_fields:
        buttons.append([KeyboardButton(text="⏭️ O'tkazib yuborish")])

    # Boshqa maydonlar
    if "notes" not in skip_fields:
        buttons.append([KeyboardButton(text="⏭️ O'tkazib yuborish")])

    # Bekor qilish tugmasi
    buttons.append([KeyboardButton(text="❌ Bekor qilish")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=False,
        one_time_keyboard=True,
    )


def back_keyboard() -> ReplyKeyboardMarkup:
    """Orqaga tugmasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="◀️ Orqaga")]
        ],
        resize_keyboard=True,
        is_persistent=False,
        one_time_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardMarkup:
    """Keyboardni olib tashlash"""
    return ReplyKeyboardMarkup(remove_keyboard=True)
