"""
i18n Middleware (TZ §9)
Foydalanuvchi tilini DBdan o'qib, har handler'ga `i18n` argumenti sifatida uzatadi.
"""
import json
import logging
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)

LOCALES_DIR = Path(__file__).parent.parent.parent / "locales"
SUPPORTED_LANGUAGES = ("uz", "ru", "tr")
DEFAULT_LANGUAGE = "uz"


class I18nMiddleware(BaseMiddleware):
    """
    Ko'p tilli qo'llab-quvvatlash middleware.
    Foydalanuvchi tilini DBdan o'qiydi va in-memory cache'da saqlaydi.
    """

    def __init__(
        self,
        get_language_func: Callable[..., Awaitable[Any]] | None = None,
    ) -> None:
        super().__init__()
        self._get_language_func = get_language_func
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._cache: Dict[int, str] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        for lang in SUPPORTED_LANGUAGES:
            locale_file = LOCALES_DIR / f"{lang}.json"
            try:
                with open(locale_file, "r", encoding="utf-8") as f:
                    self._translations[lang] = json.load(f)
            except FileNotFoundError:
                logger.warning(f"Locale file not found: {locale_file}")
                self._translations[lang] = {}
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {locale_file}: {e}")
                self._translations[lang] = {}

    def get_text(self, lang: str, key: str, **kwargs) -> str:
        """
        Kalit bo'yicha tarjima qaytaradi.
        Nested key qo'llanadi (masalan: "manager_menu.buttons.create_cargo").
        """
        translations = self._translations.get(lang) or self._translations.get(DEFAULT_LANGUAGE, {})

        keys = key.split(".")
        value: Any = translations
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                value = None
                break

        if value is None or not isinstance(value, str):
            logger.debug(f"Translation missing — lang: {lang}, key: {key}")
            return f"[{key}]"

        if kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, IndexError, ValueError) as e:
                logger.warning(f"Format error in '{key}': {e}")
                return value

        return value

    def get_user_language(self, user_id: int) -> str:
        """Cache'dan tilni olish (sync). Cache'da bo'lmasa default qaytaradi."""
        return self._cache.get(user_id, DEFAULT_LANGUAGE)

    def invalidate_cache(self, user_id: int) -> None:
        """Cache'dan tilni olib tashlash (til o'zgarganda)"""
        self._cache.pop(user_id, None)

    @staticmethod
    def _extract_user_id(event: TelegramObject) -> int | None:
        if isinstance(event, Update):
            if event.message and event.message.from_user:
                return event.message.from_user.id
            if event.callback_query and event.callback_query.from_user:
                return event.callback_query.from_user.id
            if event.inline_query and event.inline_query.from_user:
                return event.inline_query.from_user.id
        return None

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = self._extract_user_id(event)

        lang = DEFAULT_LANGUAGE
        if user_id:
            lang = self._cache.get(user_id) or DEFAULT_LANGUAGE
            if user_id not in self._cache and self._get_language_func:
                try:
                    from database.database import get_session
                    async with get_session() as session:
                        db_lang = await self._get_language_func(session, user_id)
                        if db_lang:
                            lang = db_lang
                            self._cache[user_id] = db_lang
                except Exception as e:
                    logger.error(f"DB'dan til olishda xato: {e}")

        data["i18n"] = self
        data["user_language"] = lang

        return await handler(event, data)


def init_i18n(
    get_language_func: Callable[..., Awaitable[Any]] | None = None,
) -> I18nMiddleware:
    """I18nMiddleware obyektini yaratish"""
    return I18nMiddleware(get_language_func)


# Global instance — locales/*.json ni yuklab qoldirish uchun
i18n_middleware = I18nMiddleware()


def get_text(lang: str, key: str, **kwargs) -> str:
    """Helper — global instance orqali tarjima"""
    return i18n_middleware.get_text(lang, key, **kwargs)
