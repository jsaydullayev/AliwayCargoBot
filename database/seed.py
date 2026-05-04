"""
Seed data script for Cargo Telegram Bot
Initial data: groups and company_info
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from database.database import db
from database.models import Group, CompanyInfo
from database.crud import GroupCRUD, CompanyInfoCRUD


INITIAL_GROUPS = [
    {
        "name_uz": "Erkaklar kiyimi",
        "name_ru": "Мужская одежда",
        "name_tr": "Erkek giyim",
        "telegram_link": "https://t.me/mens_clothing",
        "emoji": "👔",
        "sort_order": 1,
    },
    {
        "name_uz": "Ayollar kiyimi",
        "name_ru": "Женская одежда",
        "name_tr": "Kadın giyim",
        "telegram_link": "https://t.me/womens_clothing",
        "emoji": "👗",
        "sort_order": 2,
    },
    {
        "name_uz": "Bolalar kiyimi",
        "name_ru": "Детская одежда",
        "name_tr": "Çocuk giyim",
        "telegram_link": "https://t.me/kids_clothing",
        "emoji": "🧒",
        "sort_order": 3,
    },
    {
        "name_uz": "Oyoq kiyimlar",
        "name_ru": "Обувь",
        "name_tr": "Ayakkabılar",
        "telegram_link": "https://t.me/footwear",
        "emoji": "👟",
        "sort_order": 4,
    },
]

INITIAL_COMPANY_INFO = {
    "address_uz": "",
    "address_ru": "",
    "address_tr": "",
    "address_cn": "广州市荔湾区站前路90号广州加和城A1024铺",
    "phone_numbers": [],
    "phone_numbers_cn": ["187 1888 8827"],
    "telegram_account": "yoldashali_guanjou",
    "working_hours": "",
}


async def seed_groups(session: AsyncSession) -> None:
    """Guruhlarni bazaga qo'shish"""
    print("📚 Guruhlarni qo'shmoqda...")

    for group_data in INITIAL_GROUPS:
        existing = await GroupCRUD.get_all_active(session)
        existing_names = [g.name_uz for g in existing]

        if group_data["name_uz"] not in existing_names:
            await GroupCRUD.create(session, **group_data)
            print(f"  ✅ {group_data['name_uz']}")
        else:
            print(f"  ⏭️ {group_data['name_uz']} - allaqachon mavjud")

    print("✅ Guruhlar muvaffaqiyatli qo'shildi!\n")


async def seed_company_info(session: AsyncSession) -> None:
    """Kompaniya ma'lumotlarini bazaga qo'shish"""
    print("🏢 Kompaniya ma'lumotlarini qo'shmoqda...")

    info = await CompanyInfoCRUD.get(session)

    if not info:
        await CompanyInfoCRUD.create(session, **INITIAL_COMPANY_INFO)
        print("  ✅ Kompaniya ma'lumotlari qo'shildi")
    else:
        # Update with new data
        await CompanyInfoCRUD.update(session, **INITIAL_COMPANY_INFO)
        print("  ✅ Kompaniya ma'lumotlari yangilandi")

    print("✅ Kompaniya ma'lumotlari muvaffaqiyatli saqlandi!\n")


async def main():
    """Asosiy funksiya"""
    print("🌱 Seed data yuklashni boshlash...\n")

    async with db.async_session_maker() as session:
        try:
            await seed_groups(session)
            await seed_company_info(session)

            await session.commit()
            print("🎉 Barcha seed data muvaffaqiyatli yuklandi!")

        except Exception as e:
            await session.rollback()
            print(f"❌ Xato yuz berdi: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
