"""
Database connection test
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_db():
    """Database ga ulanish test"""
    print("Database connection test...")
    print(f"DB_HOST: {os.getenv('DB_HOST', 'localhost')}")
    print(f"DB_PORT: {os.getenv('DB_PORT', '5432')}")
    print(f"DB_NAME: {os.getenv('DB_NAME', 'cargo_db')}")
    print(f"DB_USER: {os.getenv('DB_USER', 'cargo_user')}")

    try:
        from database.database import db
        from database.models import Base
        from sqlalchemy import inspect

        # Engine yaratish
        engine = db.engine

        # Tables bor-yo'ligini tekshirish (SQLAlchemy 2.x)
        async with engine.connect() as conn:
            existing_tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )

            if existing_tables:
                print(f"\n[OK] Found {len(existing_tables)} tables in database!")
                print(f"   Tables: {', '.join(existing_tables)}")
            else:
                print("\n[WARNING] No tables found! Run migrations:")
                print("   cd d:\\AliwayBot")
                print("   alembic upgrade head")

        # Connection yopish
        await conn.close()
        print("\n[OK] Connection test passed!")

    except Exception as e:
        print(f"\n[ERROR] Connection failed: {type(e).__name__}: {e}")
        print("\nSuggestions:")
        print("1. Check if PostgreSQL server is running")
        print("2. Check .env file settings")
        print("3. Verify DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")

if __name__ == "__main__":
    asyncio.run(test_db())
