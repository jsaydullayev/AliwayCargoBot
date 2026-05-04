"""
Role Middleware (TZ §3.2)
Foydalanuvchi managermi yoki clientmi ekanini aniqlab, contextga qo'shadi.
"""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from cachetools import TTLCache

from config import settings


class RoleMiddleware(BaseMiddleware):
    """
    Manager rolini aniqlash. Cache: 10 daqiqa, max 1000 user.
    `data["is_manager"]` va `data["user_id"]` qo'shadi.
    """

    def __init__(self) -> None:
        super().__init__()
        self._cache: TTLCache = TTLCache(maxsize=1000, ttl=600)

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

        if user_id:
            if user_id in self._cache:
                is_manager = self._cache[user_id]
            else:
                is_manager = user_id in settings.MANAGER_IDS
                self._cache[user_id] = is_manager

            data["is_manager"] = is_manager
            data["user_id"] = user_id
        else:
            data["is_manager"] = False
            data["user_id"] = None

        return await handler(event, data)


role_middleware = RoleMiddleware()
