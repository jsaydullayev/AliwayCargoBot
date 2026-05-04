"""
Client klaviaturalari - Reply keyboards
"""
from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def client_menu_keyboard() -> ReplyKeyboardMarkup:
    """Client asosiy menyusi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🆔 Mening Cargo ID im"),
                KeyboardButton(text="🔍 Yukimni kuzatish"),
            ],
            [
                KeyboardButton(text="🛍️ Bizning guruhlar"),
                KeyboardButton(text="📞 Bog'lanish"),
            ],
            [
                KeyboardButton(text="⚙️ Sozlamalar")
            ]
        ],
        resize_keyboard=True,
        is_persistent=False,
    )


def contact_request_keyboard() -> ReplyKeyboardMarkup:
    """Telefon raqam so'rash keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Telefon raqamni ulashish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        is_persistent=False,
    )


def cargo_id_input_keyboard() -> ReplyKeyboardMarkup:
    """Cargo ID kiritish keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
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
    return ReplyKeyboardMarkup(keyboard=[], remove_keyboard=True)