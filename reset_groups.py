"""
Telegram guruhlarini qayta o'rnatish.

Bazadagi BARCHA guruhlarni o'chiradi va `database/seed.py` dagi INITIAL_GROUPS
ro'yxatini qayta qo'shadi. Kategoriyalarga (`group_categories`) tegilmaydi.

Ishga tushirish:
    python reset_groups.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import delete

from database.crud import GroupCRUD
from database.database import db
from database.models import Group
from database.seed import INITIAL_GROUPS


async def main() -> None:
    """Guruhlarni o'chirib, INITIAL_GROUPS ni qayta qo'shish"""
    async with db.async_session_maker() as session:
        try:
            existing = await GroupCRUD.get_all(session)
            print(f"Hozirgi guruhlar: {len(existing)} ta")
            for grp in existing:
                print(f"  - {grp.name_uz} -> {grp.telegram_link}")

            await session.execute(delete(Group))
            print("\nBarcha guruhlar o'chirildi.\n")

            for grp in INITIAL_GROUPS:
                await GroupCRUD.create(session=session, category_id=None, **grp)
                print(f"  + {grp['name_uz']} -> {grp['telegram_link']}")

            await session.commit()
            print(f"\nTayyor: {len(INITIAL_GROUPS)} ta guruh qoldi.")

        except Exception as e:
            await session.rollback()
            print(f"Xato yuz berdi: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
