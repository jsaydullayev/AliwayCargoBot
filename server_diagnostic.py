"""
Server diagnostika skripti - AliwayBot uchun
Muammolarni aniqlash va tuzatish bo'yicha tavsiyalar
"""
import sys
import os
import platform
import subprocess
from pathlib import Path

def check_python():
    """Python va versiyasini tekshirish"""
    print("🐍 Python tekshiruvi:")
    print(f"   Python versiyasi: {sys.version}")
    print(f"   Python yo'li: {sys.executable}")

    if sys.version_info < (3, 9):
        print("   ❌ Python 3.9+ talab qilinadi!")
        return False
    print("   ✅ Python versiyasi mos")
    return True

def check_os():
    """Operatsion tizimni tekshirish"""
    print("\n💻 Operatsion tizim:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Arxitektura: {platform.machine()}")
    return True

def check_env_file():
    """.env faylini tekshirish"""
    print("\n📄 .env fayli tekshiruvi:")

    env_path = Path(".env")
    if not env_path.exists():
        print("   ❌ .env fayli topilmadi!")
        print("   💡 Tavsiya: .env.example fayldan nusxa oling")
        return False

    print("   ✅ .env fayli mavjud")

    # Muhim environment variables
    required_vars = ["BOT_TOKEN", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    optional_vars = ["MANAGER_IDS", "LOG_LEVEL"]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"   ❌ {var} - o'rnatilmagan")
        else:
            # Sensitive ma'lumotlarni yashirish
            if "PASSWORD" in var or "TOKEN" in var:
                masked_value = value[:4] + "..." if len(value) > 4 else "***"
                print(f"   ✅ {var}: {masked_value}")
            else:
                print(f"   ✅ {var}: {value}")

    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"   ℹ️ {var}: {value}")

    if missing_vars:
        print(f"   ❌ Quyidagi o'zgaruvchilar o'rnatilmagan: {', '.join(missing_vars)}")
        return False

    return True

def check_postgres():
    """PostgreSQL o'rnatilganini tekshirish"""
    print("\n🐘 PostgreSQL tekshiruvi:")

    # Docker ni tekshirish
    try:
        result = subprocess.run(["docker", "--version"],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"   ✅ Docker o'rnatilgan: {result.stdout.strip()}")

            # PostgreSQL konteynerlarni tekshirish
            try:
                result = subprocess.run(["docker", "ps", "--filter", "name=postgres"],
                                      capture_output=True, text=True, timeout=5)
                if "postgres" in result.stdout.lower():
                    print("   ✅ PostgreSQL konteynerlari topildi:")
                    print(f"   {result.stdout}")
                else:
                    print("   ⚠️ PostgreSQL konteynerlari topilmadi")
            except Exception as e:
                print(f"   ⚠️ Docker konteynerlarni tekshirib bo'lmadi: {e}")
        else:
            print("   ❌ Docker o'rnatilmagan")
    except FileNotFoundError:
        print("   ❌ Docker o'rnatilmagan")

    # Native PostgreSQL ni tekshirish
    try:
        result = subprocess.run(["psql", "--version"],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"   ✅ PostgreSQL o'rnatilgan: {result.stdout.strip()}")
    except FileNotFoundError:
        print("   ℹ️  Native PostgreSQL o'rnatilmagan")

    return True

def check_database_connection():
    """Database ga ulanishni tekshirish"""
    print("\n🔗 Database ulanish tekshiruvi:")

    try:
        import asyncio
        from sqlalchemy import text
        from database.database import get_session

        async def test_connection():
            try:
                async with get_session() as session:
                    result = await session.execute(text("SELECT 1"))
                    return True
            except Exception as e:
                print(f"   ❌ Database ulanish xatosi: {e}")
                return False

        is_connected = asyncio.run(test_connection())
        if is_connected:
            print("   ✅ Database ga muvaffaqiyatli ulandi")
        return is_connected

    except ImportError as e:
        print(f"   ❌ Database modullarini import qilib bo'lmadi: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Kutilmagan xato: {e}")
        return False

def check_dependencies():
    """Python dependencies ni tekshirish"""
    print("\n📦 Dependencies tekshiruvi:")

    required_packages = [
        "aiogram",
        "sqlalchemy",
        "asyncpg",
        "alembic",
        "pydantic",
        "pydantic_settings",
        "python-dotenv"
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - o'rnatilmagan")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n   ❌ Quyidagi paketlar o'rnatilmagan: {', '.join(missing_packages)}")
        print("   💡 Tavsiya: pip install -r requirements.txt")
        return False

    return True

def check_migrations():
    """Database migratsiyalarini tekshirish"""
    print("\n🔄 Database migratsiyalari tekshiruvi:")

    try:
        import subprocess
        result = subprocess.run(["python", "-m", "alembic", "current"],
                              capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            output = result.stdout.strip()
            if "add_cn_fields" in output or "head" in output:
                print(f"   ✅ Migratsiyalar yangi: {output}")
                return True
            else:
                print(f"   ⚠️ Migratsiyalar holati: {output}")
                print("   💡 Tavsiya: python -m alembic upgrade head")
                return False
        else:
            print(f"   ❌ Migratsiyalarni tekshirib bo'lmadi: {result.stderr}")
            return False

    except Exception as e:
        print(f"   ❌ Migratsiya tekshiruv xatosi: {e}")
        return False

def main():
    """Asosiy diagnostika funksiyasi"""
    print("=" * 60)
    print("🔍 ALIWAYBOT SERVER DIAGNOSTIKASI")
    print("=" * 60)

    results = {
        "Python": check_python(),
        "OS": check_os(),
        ".env fayli": check_env_file(),
        "PostgreSQL": check_postgres(),
        "Dependencies": check_dependencies(),
        "Database ulanish": check_database_connection(),
        "Migratsiyalar": check_migrations()
    }

    print("\n" + "=" * 60)
    print("📊 NATIJALAR:")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")

    print(f"\nUmumiy: {passed}/{total} tekshiruv muvaffaqiyatli")

    if passed == total:
        print("\n🎉 Barcha tekshiruvlar muvaffaqiyatli!")
        print("🚀 Botni ishga tushirish uchun: python main.py")
    else:
        print("\n⚠️  Ba'zi muammolar topildi.")
        print("💡 Yuqoridagi tavsiyalarni amalga oshiring.")

if __name__ == "__main__":
    main()