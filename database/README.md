# Database Module - Cargo Telegram Bot

Cargo Telegram Bot database moduli uchun hujjat.

## Tuzilma

```
database/
├── __init__.py           # Modul exportlari
├── models.py              # SQLAlchemy modellari
├── crud.py                # CRUD operatsiyalari
├── database.py            # Bog'lanish boshqaruvi
├── utils/
│   ├── __init__.py
│   └── cargo_id_gen.py  # Cargo ID generatsiya qiluvchi
└── migrations/
    ├── __init__.py
    ├── env.py              # Alembic muhit sozlamalari
    ├── script.py.mako       # Migration shabloni
    └── versions/           # Migration fayllari
        ├── 20260503_0000_initial.py
```

## Modellar

### Client
Mijozlar ma'lumotlarini saqlash uchun jadval.

**Asosiy jihlat:**
- Mijozlar bilan bog'liq bo'lishi kerak
- Barcha yuklar `shipments` jadvalida saqlanadi
- Doimiy 5 xonali `cargo_id` har mijozga biriktiriladi

### Shipment
Yuklar ma'lumotlarini saqlash uchun jadval.

**Statuslar:**
- `pending` - Kutilmoqda
- `in_transit` - Yo'lda
- `arrived` - Yetib keldi
- `ready` - Tayyor
- `delivered` - Topshirildi

### Group
Savdo guruhlari ma'lumotlarini saqlash uchun jadval.

### CompanyInfo
Kompaniya ma'lumotlarini saqlash uchun jadval.

## CRUD Operatsiyalari

### client_crud
```python
# Telefon bo'yicha topish
client = await client_crud.get_by_phone(session, "+998901234567")

# Cargo ID bo'yicha topish
client = await client_crud.get_by_cargo_id(session, "48392")

# Telegram ID bo'yicha topish
client = await client_crud.get_by_telegram_id(session, 123456789)

# Yangi client yaratish
client = await client_crud.create(
    session=session,
    phone_number="+998901234567",
    cargo_id="48392",
    created_by=123456789,
    telegram_id=123456789,
    full_name="Alijon Valiyev",
    language="uz",
)

# Cargo ID yangilash
client = await client_crud.update_cargo_id(session, client_id=1, new_cargo_id="73015")

# Telegram ID biriktirish
client = await client_crud.link_telegram(session, "+998901234567", 123456789)

# Client tilini yangilash
client = await client_crud.update_language(session, 123456789, "ru")
```

### shipment_crud
```python
# ID bo'yicha yukni topish
shipment = await shipment_crud.get_by_id(session, 1)

# Client yuklarini olish
shipments = await shipment_crud.get_by_client(session, client_id=1)

# Cargo ID bo'yicha yuklarni olish
shipments = await shipment_crud.get_by_cargo_id(session, "48392")

# Status bo'yicha filtrlash
shipments = await shipment_crud.get_by_status(session, CargoStatus.IN_TRANSIT)

# Yangi yuk yaratish
shipment = await shipment_crud.create(
    session=session,
    client_id=1,
    description="Kiyim-kechak",
    weight_kg=25.5,
    cargo_weight_kg=120.0,
    price=450.00,
    currency="USD",
    photo_file_id="AgACAgIA...",
    notes="Ehtiyotkorlik bilan",
    created_by=123456789,
)

# Status yangilash
shipment = await shipment_crud.update_status(session, shipment_id=1, status=CargoStatus.DELIVERED)
```

### group_crud
```python
# Faol guruhlarni olish
groups = await group_crud.get_all_active(session)

# Yangi guruh yaratish
group = await group_crud.create(
    session=session,
    name_uz="Erkaklar kiyimi",
    name_ru="Мужская одежда",
    name_tr="Erkek giyim",
    telegram_link="https://t.me/...",
    emoji="👔",
    sort_order=1,
)
```

## Cargo ID Generatsiya

```python
from database.utils import cargo_id_generator

# Unikal 5 xonali ID yaratish
cargo_id = await cargo_id_generator.generate_unique_id(session)

# ID bandligini tekshirish
is_available = await cargo_id_generator.is_id_available(session, "48392")
```

## Migratsiyalar

### Migration yaratish
```bash
# Yangi migration
alembic revision -m "Migration description"

# Autogenerate (bog'lanish kerak)
alembic revision --autogenerate -m "Description"
```

### Migrationni qo'llash
```bash
# Barcha migratsiyalarni q'llash
alembic upgrade head

# Oxirgi migrationgacha
alembic upgrade +revision_id

# 1 tagga qaytarish
alembic downgrade -1
```

## Bog'lanish Sozlamalari

`.env` faylida quyidagi o'zgaruvchilar talab qilinadi:

```env
# Database (PostgreSQL)
DB_HOST=postgres          # Docker uchun
DB_HOST=localhost          # Local uchun
DB_PORT=5432
DB_NAME=cargo_db
DB_USER=cargo_user
DB_PASSWORD=password

# Connection Pool
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=15

# Debug
DB_ECHO=false
```

## Test qilish

```bash
# Database test scriptini ishga tushirish
python test_db.py
```

Test quyidagilarni tekshiradi:
1. Database bilan bog'lanish
2. Cargo ID generatsiya
3. CRUD operatsiyalari

## Seed Data

Boshlang'ich guruhlar va kompaniya ma'lumotlarini bazaga qo'shish:

```bash
# Seed scriptini ishga tushirish
python -m database.seed
```

## Qo'llab-quvvatlangan Tillar

- `uz` - O'zbekcha
- `ru` - Ruscha
- `tr` - Turkcha

Tillarni o'zgartirish uchun `locales/` katalogiga mos JSON fayllar qo'shiladi.
