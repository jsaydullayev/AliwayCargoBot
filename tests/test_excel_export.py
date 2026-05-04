"""
Excel export funksiyasini test qilish
"""
import asyncio
from datetime import datetime
from openpyxl import Workbook

from database.models import Client, Shipment, CargoStatus


# Mock data yaratish
def create_mock_shipments():
    """Test uchun mock shipment yaratish"""
    client = Client(
        id=1,
        telegram_id=123456789,
        phone_number="+998901234567",
        cargo_id="12345",
        full_name="Test User",
        language="uz",
        created_at=datetime.now(),
        created_by=999999999
    )

    shipments = [
        Shipment(
            id=1,
            client_id=1,
            description="Kiyim-kechak",
            weight_kg=25.5,
            cargo_weight_kg=30.0,
            price=450.00,
            currency="USD",
            photo_file_id="AgACAgIAAxkBAAIE...photo_id",
            status=CargoStatus.IN_TRANSIT,
            notes="Ehtiyotkorlik bilan",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=999999999,
            client=client
        ),
        Shipment(
            id=2,
            client_id=1,
            description="Elektronika",
            weight_kg=10.0,
            cargo_weight_kg=15.0,
            price=200.00,
            currency="USD",
            photo_file_id=None,
            status=CargoStatus.PENDING,
            notes=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=999999999,
            client=client
        ),
    ]

    return shipments


async def test_excel_export():
    """Excel export funksiyasini test qilish"""
    from bot.utils.excel_export import generate_excel_file

    print("🔄 Excel export testi boshlandi...")

    # Mock shipments
    shipments = create_mock_shipments()
    print(f"📦 {len(shipments)} ta mock shipment yaratildi")

    try:
        # Excel fayl generatsiya
        result = generate_excel_file(shipments)

        print(f"✅ Excel fayl muvaffaqiyatli generatsiya qilindi!")
        print(f"📁 Fayl nomi: {result.filename}")
        print(f"📊 Fayl kattaligi: {len(result.file)} bytes")

        # Faylni diskka saqlash (test uchun)
        with open(f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", "wb") as f:
            f.write(result.file)

        print(f"💾 Fayl diskka saqlandi: test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        print("\n🎉 Barcha testlar muvaffaqiyatli o'tdi!")

    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_excel_export())
