"""
Seed data script for Cargo Telegram Bot
Initial data: group categories, groups (with telegram links), and company_info
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from database.database import db
from database.models import Group, GroupCategory, CompanyInfo
from database.crud import GroupCategoryCRUD, GroupCRUD, CompanyInfoCRUD


# 3 ta asosiy kategoriya
INITIAL_CATEGORIES = [
    {
        "name_uz": "Erkaklar",
        "name_ru": "Мужчины",
        "name_tr": "Erkekler",
        "emoji": "👔",
        "sort_order": 1,
    },
    {
        "name_uz": "Ayollar",
        "name_ru": "Женщины",
        "name_tr": "Kadınlar",
        "emoji": "👗",
        "sort_order": 2,
    },
    {
        "name_uz": "Bolalar",
        "name_ru": "Дети",
        "name_tr": "Çocuklar",
        "emoji": "🧒",
        "sort_order": 3,
    },
]


# Har bir kategoriya uchun guruhlar (kategoriya `name_uz` bilan bog'lanadi)
INITIAL_GROUPS = {
    "Erkaklar": [
        {
            "name_uz": "Premium kiyimlar",
            "name_ru": "Премиум одежда",
            "name_tr": "Premium giyim",
            "emoji": "👔",
            "telegram_link": "https://t.me/aliwayerkakpremium",
            "sort_order": 1,
        },
        {
            "name_uz": "Economy kiyimlar",
            "name_ru": "Эконом одежда",
            "name_tr": "Economy giyim",
            "emoji": "🛒",
            "telegram_link": "https://t.me/bazarchimenwear",
            "sort_order": 2,
        },
        {
            "name_uz": "Oyoq kiyimlar",
            "name_ru": "Обувь",
            "name_tr": "Ayakkabılar",
            "emoji": "👞",
            "telegram_link": "https://t.me/bazarchimensshoes",
            "sort_order": 3,
        },
    ],
    "Ayollar": [
        {
            "name_uz": "Premium kiyimlar",
            "name_ru": "Премиум одежда",
            "name_tr": "Premium giyim",
            "emoji": "👗",
            "telegram_link": "https://t.me/bazarchiwomenwear",
            "sort_order": 1,
        },
        {
            "name_uz": "Economy kiyimlar",
            "name_ru": "Эконом одежда",
            "name_tr": "Economy giyim",
            "emoji": "🛍️",
            "telegram_link": "https://t.me/aliwaywomen",
            "sort_order": 2,
        },
        {
            "name_uz": "Oyoq kiyimlar",
            "name_ru": "Обувь",
            "name_tr": "Ayakkabılar",
            "emoji": "👠",
            "telegram_link": "https://t.me/ayollarshoes",
            "sort_order": 3,
        },
        {
            "name_uz": "Uy kiyimlari (Pijama)",
            "name_ru": "Домашняя одежда (пижама)",
            "name_tr": "Ev giyimi (Pijama)",
            "emoji": "🌙",
            "telegram_link": "https://t.me/aliwayichkikiyimlar",
            "sort_order": 4,
        },
    ],
    "Bolalar": [
        {
            "name_uz": "Bolalar kiyimlari",
            "name_ru": "Детская одежда",
            "name_tr": "Çocuk giyimi",
            "emoji": "🧒",
            "telegram_link": "https://t.me/bazarchikidswear",
            "sort_order": 1,
        },
        {
            "name_uz": "Bolalar oyoq kiyimlari",
            "name_ru": "Детская обувь",
            "name_tr": "Çocuk ayakkabıları",
            "emoji": "👟",
            "telegram_link": "https://t.me/aliwaykidsshoes",
            "sort_order": 2,
        },
    ],
}


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


async def seed_categories(session: AsyncSession) -> dict:
    """Kategoriyalarni bazaga qo'shish (idempotent). name_uz → category obyekt mapping qaytaradi."""
    print("📂 Kategoriyalarni qo'shmoqda...")

    existing = await GroupCategoryCRUD.get_all(session)
    name_to_cat = {c.name_uz: c for c in existing}

    for cat_data in INITIAL_CATEGORIES:
        if cat_data["name_uz"] not in name_to_cat:
            created = await GroupCategoryCRUD.create(session, **cat_data)
            name_to_cat[created.name_uz] = created
            print(f"  ✅ {cat_data['name_uz']}")
        else:
            print(f"  ⏭️ {cat_data['name_uz']} - allaqachon mavjud")

    print("✅ Kategoriyalar tayyor!\n")
    return name_to_cat


async def seed_groups(session: AsyncSession, categories: dict) -> None:
    """Har bir kategoriya uchun guruhlarni qo'shish (idempotent — telegram_link bo'yicha tekshiriladi)."""
    print("🛍️ Guruhlarni qo'shmoqda...")

    existing = await GroupCRUD.get_all(session)
    existing_links = {g.telegram_link for g in existing}

    for cat_name, groups in INITIAL_GROUPS.items():
        category = categories.get(cat_name)
        if not category:
            print(f"  ⚠️ Kategoriya '{cat_name}' topilmadi — guruhlar o'tkazib yuborildi")
            continue

        for grp in groups:
            if grp["telegram_link"] in existing_links:
                print(f"  ⏭️ {cat_name} → {grp['name_uz']} (link mavjud)")
                continue
            await GroupCRUD.create(session=session, category_id=category.id, **grp)
            print(f"  ✅ {cat_name} → {grp['emoji']} {grp['name_uz']}")

    print("✅ Guruhlar tayyor!\n")


async def seed_company_info(session: AsyncSession) -> None:
    """Kompaniya ma'lumotlarini bazaga qo'shish"""
    print("🏢 Kompaniya ma'lumotlarini qo'shmoqda...")

    info = await CompanyInfoCRUD.get(session)

    if not info:
        await CompanyInfoCRUD.create(session, **INITIAL_COMPANY_INFO)
        print("  ✅ Kompaniya ma'lumotlari qo'shildi")
    else:
        await CompanyInfoCRUD.update(session, **INITIAL_COMPANY_INFO)
        print("  ✅ Kompaniya ma'lumotlari yangilandi")

    print("✅ Kompaniya ma'lumotlari saqlandi!\n")


async def main():
    """Asosiy funksiya"""
    print("🌱 Seed data yuklashni boshlash...\n")

    async with db.async_session_maker() as session:
        try:
            categories = await seed_categories(session)
            await seed_groups(session, categories)
            await seed_company_info(session)

            await session.commit()
            print("🎉 Barcha seed data muvaffaqiyatli yuklandi!")

        except Exception as e:
            await session.rollback()
            print(f"❌ Xato yuz berdi: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
