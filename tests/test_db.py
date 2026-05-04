"""
Database connection test script
"""
import asyncio
import sys
import os

from dotenv import load_dotenv

load_dotenv()

from database.database import db, get_session
from database.models import Client, Shipment, Group, CompanyInfo, CargoStatus
from database.crud import client_crud, shipment_crud, group_crud
from database.utils import cargo_id_generator


async def test_database_connection():
    """Database bilan bog'lanishni tekshirish"""
    print("🔌 Database bilan bog'lanishni tekshirish...")
    try:
        # Test connection
        async with get_session() as session:
            result = await session.execute("SELECT 1")
            print(f"✅ Database bilan bog'landi: {result.scalar()}")
        return True
    except Exception as e:
        print(f"❌ Database bilan bog'lanishda xato: {e}")
        return False


async def test_cargo_id_generation():
    """Cargo ID generatsiyasini tekshirish"""
    print("\n🆔 Cargo ID generatsiyasini tekshirish...")
    try:
        async with get_session() as session:
            cargo_id = await cargo_id_generator.generate_unique_id(session)
            print(f"✅ Yangi Cargo ID generatsiya qilindi: {cargo_id}")
            return cargo_id
    except Exception as e:
        print(f"❌ Cargo ID generatsiyasida xato: {e}")
        return None


async def test_crud_operations():
    """CRUD operatsiyalarini tekshirish"""
    print("\n🧪 CRUD operatsiyalarini tekshirish...")
    async with get_session() as session:
        try:
            # Test: Create client
            print("  📝 Yangi client yaratish...")
            cargo_id = await cargo_id_generator.generate_unique_id(session)
            client = await client_crud.create(
                session=session,
                phone_number="+998901234567",
                cargo_id=cargo_id,
                created_by=123456789,
                telegram_id=123456789,
                full_name="Test User",
                language="uz",
            )
            print(f"    ✅ Client yaratildi: {client.full_name}, Cargo ID: {client.cargo_id}")

            # Test: Get client by phone
            print("  🔍 Clientni telefon raqami bo'yicha qidirish...")
            found_client = await client_crud.get_by_phone(session, "+998901234567")
            print(f"    ✅ Client topildi: {found_client.full_name if found_client else 'Yo\'q'}")

            # Test: Create shipment
            print("  📦 Yangi yuk biriktirish...")
            shipment = await shipment_crud.create(
                session=session,
                client_id=client.id,
                description="Test yuk - Kiyim-kechak",
                created_by=123456789,
                weight_kg=25.5,
                cargo_weight_kg=120.0,
                price=450.00,
                currency="USD",
            )
            print(f"    ✅ Yuk biriktirildi: {shipment.description}, Status: {shipment.status}")

            # Test: Get shipments by client
            print("  📋 Client yuklarini olish...")
            shipments = await shipment_crud.get_by_client(session, client.id)
            print(f"    ✅ {len(shipments)} ta yuk topildi")

            # Test: Update shipment status
            print("  🔄 Yuk statusini yangilash...")
            updated_shipment = await shipment_crud.update_status(
                session=session,
                shipment_id=shipment.id,
                status=CargoStatus.IN_TRANSIT,
            )
            print(f"    ✅ Status yangilandi: {updated_shipment.status}")

            # Test: Get active groups
            print("  📚 Faol guruhlarni olish...")
            groups = await group_crud.get_all_active(session)
            print(f"    ✅ {len(groups)} ta guruh topildi")
            for group in groups[:2]:  # Show first 2
                print(f"       - {group.emoji} {group.name_uz}")

            # Rollback test data
            await session.rollback()
            print("  🔄 Test ma'lumotlari rollback qilindi")

            print("✅ CRUD operatsiyalari muvaffaqiyatli tugadi!")
            return True

        except Exception as e:
            print(f"❌ CRUD operatsiyalarida xato: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Asosiy test funksiyasi"""
    print("=" * 50)
    print("🧪 DATABASE TEST SCRIPT")
    print("=" * 50)

    # Check environment variables
    print("\n🔑 Muhit o'zgaruvchilarini tekshirish...")
    required_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"⚠️ Quyidagi o'zgaruvchilar .env faylida yo'q: {', '.join(missing_vars)}")
        print("   .env.example faylini nusxalab, to'ldiring: cp .env.example .env\n")
        return

    print("✅ Barcha muhit o'zgaruvchari mavjud")

    # Run tests
    connection_ok = await test_database_connection()
    if not connection_ok:
        return

    await test_cargo_id_generation()
    await test_crud_operations()

    print("\n" + "=" * 50)
    print("✅ BARCHA TESTLAR MUVAFFAQIYATLI TUGADI!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
