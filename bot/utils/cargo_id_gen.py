"""
Cargo ID generator utility
TZ §5.2 — 5 xonali unikal Cargo ID generatsiyasi (00000-99999, faqat raqamlar)
"""
import logging
import random

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Client

logger = logging.getLogger(__name__)

ID_MIN = 0
ID_MAX = 99999
MAX_RETRIES = 50


class CargoIDGenerator:
    """5 xonali unikal Cargo ID generatori"""

    @staticmethod
    async def generate_unique_id(session: AsyncSession) -> str:
        """
        Random 5-xonali Cargo ID generatsiya qiladi va DB orqali unikalligi tekshiriladi.
        Random + retry pattern — barcha mavjud ID'larni xotiraga yuklamaydi.

        Returns:
            5 xonali string formatida Cargo ID (masalan: "48392", "00007")

        Raises:
            RuntimeError: Agar barcha ID lar band bo'lib qolgan bo'lsa
        """
        for attempt in range(MAX_RETRIES):
            candidate = f"{random.randint(ID_MIN, ID_MAX):05d}"

            if await CargoIDGenerator.is_id_available(session, candidate):
                return candidate

        # Retry tugadi — DB juda to'lib qolgan, sequential search
        logger.warning(f"{MAX_RETRIES} ta random urinish muvaffaqiyatsiz, sequential search'ga o'tildi")

        result = await session.execute(
            select(Client.cargo_id).where(Client.cargo_id.is_not(None))
        )
        existing = set(result.scalars().all())

        for candidate_int in range(ID_MIN, ID_MAX + 1):
            candidate = f"{candidate_int:05d}"
            if candidate not in existing:
                return candidate

        raise RuntimeError("Barcha Cargo ID lar band bo'lib qolgan (00000-99999 to'lgan)")

    @staticmethod
    async def is_id_available(session: AsyncSession, cargo_id: str) -> bool:
        """
        Cargo ID DBda mavjud emasligini tekshirish

        Args:
            session: AsyncSession
            cargo_id: Tekshirilayotgan Cargo ID

        Returns:
            True — band emas, False — band
        """
        result = await session.execute(
            select(func.count(Client.id)).where(Client.cargo_id == cargo_id)
        )
        count = result.scalar() or 0
        return count == 0


cargo_id_generator = CargoIDGenerator()
