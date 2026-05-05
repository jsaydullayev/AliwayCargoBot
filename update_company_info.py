"""
Update company info in database
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import db
from database.crud import CompanyInfoCRUD

COMPANY_INFO = {
    "address_uz": "",
    "address_ru": "",
    "address_tr": "",
    "address_cn": "广州市荔湾区站前路90号广州加和城A1024铺",
    "phone_numbers": [],
    "phone_numbers_cn": ["187 1888 8827"],
    "telegram_account": "yoldashali_guanjou",
    "working_hours": "",
}


async def main():
    """Asosiy funksiya"""
    print("Updating company info...\n")

    async with db.async_session_maker() as session:
        try:
            info = await CompanyInfoCRUD.get(session)

            if info:
                await CompanyInfoCRUD.update(session, **COMPANY_INFO)
                print("Company info updated")
            else:
                await CompanyInfoCRUD.create(session, **COMPANY_INFO)
                print("Company info created")

            await session.commit()
            print("\nData saved successfully!")

        except Exception as e:
            await session.rollback()
            print(f"Error occurred: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
