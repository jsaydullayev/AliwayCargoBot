# 📦 TEXNIK TOPSHIRIQ (TZ)

## Cargo Telegram Bot

---

**Hujjat versiyasi:** 1.1  
**Sana:** 2025  
**Holat:** Tasdiqlash uchun  
**O'zgarishlar (v1.1):** Cargo ID logikasi qayta ko'rib chiqildi — ID yukka emas, mijozga biriktiriladi. Ma'lumotlar modeli va manager flow yangilandi.

---

## MUNDARIJA

1. [Loyiha haqida umumiy ma'lumot](#1-loyiha-haqida-umumiy-malumot)
2. [Texnologik stek](#2-texnologik-stek)
3. [Foydalanuvchi rollari](#3-foydalanuvchi-rollari)
4. [Ma'lumotlar modeli](#4-malumotlar-modeli)
5. [Manager paneli — Funksional talablar](#5-manager-paneli--funksional-talablar)
6. [Client paneli — Funksional talablar](#6-client-paneli--funksional-talablar)
7. [Bot scenariylari (Flows)](#7-bot-scenariylari-flows)
8. [Xabarnoma tizimi](#8-xabarnoma-tizimi)
9. [Ko'p tilli qo'llab-quvvatlash](#9-kop-tilli-qollab-quvvatlash)
10. [Acceptance Criteria](#10-acceptance-criteria)
11. [Non-funksional talablar](#11-non-funksional-talablar)
12. [Deployment](#12-deployment)

---

## 1. Loyiha haqida umumiy ma'lumot

### 1.1 Maqsad

Cargo kompaniyasi uchun Telegram bot ishlab chiqish. Bot orqali manager har bir mijozga **doimiy 5 xonali Cargo ID** beradi. Bu ID mijozga bir marta biriktiriladi va keyingi barcha yuklarida ham shu ID ishlatiladi. Har bir yuk alohida yozuv (shipment) sifatida saqlanadi. Manager yuk ma'lumotlarini boshqaradi, bazani Excel formatida eksport qiladi. Mijoz esa o'z doimiy Cargo ID si orqali barcha yuklarini kuzatib boradi.

### 1.2 Asosiy funksiyalar

| #   | Funksiya                                   | Rol     |
| --- | ------------------------------------------ | ------- |
| 1   | 5 xonali unikal Cargo ID yaratish          | Manager |
| 2   | Yuk ma'lumotlarini qo'shish va yangilash   | Manager |
| 3   | Yuk statusini o'zgartirish                 | Manager |
| 4   | Bazani Excel formatida eksport qilish      | Manager |
| 5   | Cargo ID orqali yuk ma'lumotlarini ko'rish | Client  |
| 6   | O'z Cargo ID sini ko'rish                  | Client  |
| 7   | Savdo guruhlariga kirish                   | Client  |
| 8   | Status o'zgarganda avtomatik xabarnoma     | Tizim   |
| 9   | Kompaniya aloqa ma'lumotlarini ko'rish     | Client  |

### 1.3 Loyiha chegaralari

**Kiradi:**

- Telegram bot (aiogram framework)
- PostgreSQL ma'lumotlar bazasi
- Excel eksport funksiyasi
- Ko'p tilli interfeys (O'zbekcha, Ruscha, Turkcha)
- Avtomatik push-notification tizimi

**Kirmaydi:**

- Web admin panel
- To'lov tizimi integratsiyasi
- Mobil ilova

---

## 2. Texnologik stek

| Komponent          | Texnologiya             | Versiya |
| ------------------ | ----------------------- | ------- |
| Dasturlash tili    | Python                  | 3.11+   |
| Bot framework      | aiogram                 | 3.x     |
| Ma'lumotlar bazasi | PostgreSQL              | 15+     |
| ORM                | SQLAlchemy (async)      | 2.x     |
| Migration          | Alembic                 | latest  |
| Excel eksport      | openpyxl                | latest  |
| Konfiguratsiya     | python-dotenv           | latest  |
| Konteynerizatsiya  | Docker + Docker Compose | latest  |
| Hosting            | VPS (Linux)             | —       |

### 2.1 Loyiha tuzilmasi

```
cargo_bot/
├── bot/
│   ├── handlers/
│   │   ├── manager/
│   │   │   ├── create_cargo.py
│   │   │   ├── manage_cargo.py
│   │   │   └── export.py
│   │   └── client/
│   │       ├── track.py
│   │       ├── groups.py
│   │       └── contacts.py
│   ├── keyboards/
│   │   ├── manager_kb.py
│   │   └── client_kb.py
│   ├── middlewares/
│   │   ├── role_middleware.py
│   │   └── i18n_middleware.py
│   └── utils/
│       ├── cargo_id_gen.py
│       ├── notifications.py
│       └── excel_export.py
├── database/
│   ├── models.py
│   ├── crud.py
│   └── migrations/
├── locales/
│   ├── uz.json
│   ├── ru.json
│   └── tr.json
├── config.py
├── main.py
├── docker-compose.yml
├── Dockerfile
└── .env
```

---

## 3. Foydalanuvchi rollari

### 3.1 Rollar jadvali

| Xususiyat                     | Manager               | Client        |
| ----------------------------- | --------------------- | ------------- |
| Autentifikatsiya              | Telegram ID whitelist | Ochiq (hamma) |
| Cargo ID yaratish             | ✅                    | ❌            |
| Yuk ma'lumotlarini tahrirlash | ✅                    | ❌            |
| Status o'zgartirish           | ✅                    | ❌            |
| Excel eksport                 | ✅                    | ❌            |
| Cargo ID orqali qidirish      | ✅                    | ✅            |
| O'z Cargo ID sini ko'rish     | —                     | ✅            |
| Guruh havolalarini ko'rish    | ❌                    | ✅            |
| Kompaniya aloqasini ko'rish   | ❌                    | ✅            |

### 3.2 Manager autentifikatsiyasi

- Managerlar Telegram ID lari asosida aniqlanadi
- Manager Telegram ID lari `.env` faylida `MANAGER_IDS` o'zgaruvchisida saqlanadi
- Boshqa foydalanuvchilar manager buyruqlariga kirishga harakat qilsa, tizim ruxsat beradi emas

```env
MANAGER_IDS=123456789,987654321
```

### 3.3 Client identifikatsiyasi

- Client ro'yxatdan o'tishi shart emas
- Client birinchi marta `/start` bosganida telefon raqami so'raladi
- Telefon raqami orqali client bir nechta safar yuk jo'natsa ham bitta profil ostida bo'ladi
- Har bir yuk alohida Cargo ID ga ega bo'ladi

---

## 4. Ma'lumotlar modeli

### 4.1 `clients` jadvali

> ⚠️ **Asosiy qoida:** Cargo ID **mijozga biriktiriladi**, yukka emas. Har bir mijozning bitta doimiy Cargo ID si bo'ladi. Barcha yuklar shu ID ostida `shipments` jadvalida saqlanadi.

| Ustun          | Turi                    | Tavsif                                                       |
| -------------- | ----------------------- | ------------------------------------------------------------ |
| `id`           | BIGSERIAL PK            | Ichki ID                                                     |
| `telegram_id`  | BIGINT UNIQUE NULL      | Telegram foydalanuvchi ID (bot orqali kirganda to'ldiriladi) |
| `phone_number` | VARCHAR(20) UNIQUE      | Telefon raqami — asosiy identifikator                        |
| `cargo_id`     | VARCHAR(5) UNIQUE       | **Doimiy 5 xonali Cargo ID**                                 |
| `full_name`    | VARCHAR(255) NULL       | To'liq ism                                                   |
| `language`     | VARCHAR(5) DEFAULT 'uz' | Til: `uz`, `ru`, `tr`                                        |
| `created_at`   | TIMESTAMP               | Ro'yxatdan o'tgan vaqt                                       |
| `created_by`   | BIGINT                  | Qaysi manager qo'shgani                                      |

**Cargo ID logikasi:**

- Manager telefon raqam kiritganda tizim `clients.phone_number` bo'yicha qidiradi
- **Topilsa** → mavjud `cargo_id` qaytariladi, yangi ID yaratilmaydi
- **Topilmasa** → yangi client yozuvi va yangi `cargo_id` yaratiladi
- Manager **majburan yangi ID** yaratmoqchi bo'lsa → bot tasdiqlash so'raydi (5.2 bo'lim)

### 4.2 `shipments` jadvali

> Bir client uchun vaqt o'tib bir nechta yuk bo'lishi mumkin. Har bir yuk — alohida `shipment` yozuvi.

| Ustun             | Turi                   | Tavsif                                 |
| ----------------- | ---------------------- | -------------------------------------- |
| `id`              | BIGSERIAL PK           | Ichki ID                               |
| `client_id`       | BIGINT FK → clients.id | Mijoz (cargo_id orqali ham qidiriladi) |
| `description`     | TEXT                   | Yuk nimaligi                           |
| `weight_kg`       | DECIMAL(10,2)          | Yuk kilosi (kg)                        |
| `cargo_weight_kg` | DECIMAL(10,2)          | Cargo kilosi (umumiy)                  |
| `price`           | DECIMAL(12,2)          | Narxi                                  |
| `currency`        | VARCHAR(5)             | Valyuta: `USD`, `UZS`                  |
| `photo_file_id`   | TEXT                   | Telegram file_id (rasm)                |
| `status`          | ENUM                   | Yuk holati                             |
| `notes`           | TEXT NULL              | Qo'shimcha izoh                        |
| `created_at`      | TIMESTAMP              | Yaratilgan vaqt                        |
| `updated_at`      | TIMESTAMP              | Oxirgi yangilangan vaqt                |
| `created_by`      | BIGINT                 | Manager Telegram ID                    |

**Munosabat diagrammasi:**

```
clients (1) ────────── (∞) shipments
  cargo_id  ←── Manager kiritadi
  phone_number ←── Asosiy identifikator
```

### 4.3 Status ENUM qiymatlari

```sql
CREATE TYPE cargo_status AS ENUM (
    'pending',      -- Kutilmoqda
    'in_transit',   -- Yo'lda
    'arrived',      -- Yetib keldi
    'ready',        -- Tayyor (olib ketish mumkin)
    'delivered'     -- Topshirildi
);
```

| Status       | O'zbekcha      | Ruscha       | Turkcha          |
| ------------ | -------------- | ------------ | ---------------- |
| `pending`    | 🕐 Kutilmoqda  | 🕐 Ожидается | 🕐 Bekleniyor    |
| `in_transit` | 🚚 Yo'lda      | 🚚 В пути    | 🚚 Yolda         |
| `arrived`    | 📦 Yetib keldi | 📦 Прибыло   | 📦 Ulaştı        |
| `ready`      | ✅ Tayyor      | ✅ Готово    | ✅ Hazır         |
| `delivered`  | 🎉 Topshirildi | 🎉 Выдано    | 🎉 Teslim edildi |

### 4.4 `groups` jadvali

| Ustun           | Turi         | Tavsif                  |
| --------------- | ------------ | ----------------------- |
| `id`            | SERIAL PK    | Ichki ID                |
| `name_uz`       | VARCHAR(255) | Guruh nomi (O'zbekcha)  |
| `name_ru`       | VARCHAR(255) | Guruh nomi (Ruscha)     |
| `name_tr`       | VARCHAR(255) | Guruh nomi (Turkcha)    |
| `telegram_link` | TEXT         | Telegram guruh havolasi |
| `emoji`         | VARCHAR(10)  | Emoji belgisi           |
| `is_active`     | BOOLEAN      | Ko'rsatiladimi          |
| `sort_order`    | INT          | Tartib                  |

> **Boshlang'ich guruhlar:** Erkaklar kiyimi, Ayollar kiyimi, Bolalar kiyimi, Oyoq kiyimlar

### 4.5 `company_info` jadvali

| Ustun              | Turi         | Tavsif                     |
| ------------------ | ------------ | -------------------------- |
| `id`               | SERIAL PK    | —                          |
| `address_uz`       | TEXT         | Manzil (O'zbekcha)         |
| `address_ru`       | TEXT         | Manzil (Ruscha)            |
| `address_tr`       | TEXT         | Manzil (Turkcha)           |
| `phone_numbers`    | TEXT[]       | Telefon raqamlari ro'yxati |
| `telegram_account` | VARCHAR(255) | Telegram username          |
| `working_hours`    | VARCHAR(255) | Ish vaqti                  |

---

## 5. Manager paneli — Funksional talablar

### 5.1 Manager asosiy menyusi

```
📊 Manager Panel
├── ➕ Yangi Cargo ID yaratish
├── 📦 Yuk biriktirish
├── 🔄 Status yangilash
├── 🔍 Yuklarni ko'rish
└── 📥 Excel eksport
```

### 5.2 Yangi Cargo ID yaratish / Mijoz qo'shish

**Jarayon:**

```
Manager: ➕ Yangi Cargo ID yaratish
  └─► Bot: Mijoz telefon raqamini kiriting
        └─► Manager: +998901234567
              │
              ├─► [HOLAT A] Bazada TOPILMADI
              │     └─► Yangi client yozuvi yaratiladi
              │           └─► Yangi 5 xonali Cargo ID generatsiya qilinadi
              │                 └─► Bot: ✅ Yangi mijoz qo'shildi
              │                          🆔 Cargo ID: 48392
              │
              └─► [HOLAT B] Bazada TOPILDI
                    └─► Bot: ⚠️ Bu mijoz allaqachon bazada mavjud!
                              👤 Ismi: Alijon Valiyev
                              🆔 Mavjud Cargo ID: 48392
                              📅 Ro'yxatdan o'tgan: 12.03.2025
                              ─────────────────────────
                              Nima qilmoqchisiz?
                              [📋 Mavjud IDni ishlatish] [➕ Yangi ID yaratish]
                                      │                          │
                                      │                          └─► Bot: ⚠️ Tasdiqlash
                                      │                                    Mijozning eski ID si: 48392
                                      │                                    Yangi ID yaratsak, eski ID
                                      │                                    o'chirilmaydi, lekin mijozning
                                      │                                    asosiy ID si yangilanadi.
                                      │                                    Davom etasizmi?
                                      │                                    [✅ Ha, yangi ID yarat] [❌ Bekor qilish]
                                      │                                           │
                                      │                                           └─► Yangi ID yaratiladi
                                      │                                                 └─► Bot: ✅ Yangi Cargo ID: 73015
                                      │
                                      └─► Bot: ✅ Mavjud ID: 48392
                                                Yuk biriktirish uchun shu IDdan foydalaning.
```

**Cargo ID generatsiya qoidalari:**

- Faqat raqamlardan iborat: `[0-9]{5}` (00000 dan 99999 gacha)
- Bazadagi barcha mavjud ID lar bilan taqqoslanadi — collision yo'q
- Yangi ID avvalgi ID o'rniga `clients.cargo_id` ga yoziladi
- Eski ID tarixda (`shipments` jadvalida) saqlanib qoladi

### 5.3 Yuk ma'lumotlarini biriktirish

**Jarayon:**

1. Manager `📦 Yuk biriktirish` → Cargo ID kiritadi (masalan: `48392`)
2. Tizim clientni topadi va ism + telefonini ko'rsatadi (tasdiqlash uchun)
3. Bot ketma-ket so'raydi:

| #   | Maydon                              | Majburiy | O'tkazib yuborish |
| --- | ----------------------------------- | -------- | ----------------- |
| 1   | Yuk nimaligi (text)                 | ✅ Ha    | ❌ Yo'q           |
| 2   | Yuk kilosi, kg (raqam)              | ❌       | ⏭️ tugma bor      |
| 3   | Cargo kilosi, kg (raqam)            | ❌       | ⏭️ tugma bor      |
| 4   | Narxi (raqam)                       | ❌       | ⏭️ tugma bor      |
| 5   | Valyuta (USD / UZS — inline button) | ❌       | ⏭️ tugma bor      |
| 6   | Rasmi (photo)                       | ❌       | ⏭️ tugma bor      |
| 7   | Qo'shimcha izoh (text)              | ❌       | ⏭️ tugma bor      |

> ⚠️ **Yagona majburiy maydon:** "Yuk nimaligi" — bu bo'sh qoldirilishi mumkin emas. Manager matn kiritmay davom etmoqchi bo'lsa, bot qayta so'raydi. 4. Barcha ma'lumotlar kiritilgach, preview ko'rsatiladi 5. Manager tasdiqlaydi → `shipments` jadvaliga yangi yozuv qo'shiladi

> 💡 Bir cargo ID ga vaqt o'tib bir nechta yuk biriktirilishi mumkin. Har biri alohida shipment yozuvi bo'ladi.

**Validatsiya qoidalari:**

| Maydon       | Qoida                                                                   |
| ------------ | ----------------------------------------------------------------------- |
| Cargo ID     | Bazada mavjud bo'lishi shart                                            |
| Yuk nimaligi | **Majburiy** — bo'sh bo'lmasligi kerak, o'tkazib yuborib bo'lmaydi      |
| Yuk kilosi   | Ixtiyoriy — kiritilsa 0 dan katta musbat son bo'lishi shart             |
| Cargo kilosi | Ixtiyoriy — kiritilsa 0 dan katta musbat son bo'lishi shart             |
| Narxi        | Ixtiyoriy — kiritilsa 0 dan katta musbat son bo'lishi shart             |
| Valyuta      | Ixtiyoriy — narxi kiritilgan bo'lsa ko'rsatiladi, aks holda o'tkaziladi |
| Rasm         | Ixtiyoriy — Telegram photo formati                                      |
| Izoh         | Ixtiyoriy — istalgan matn                                               |

### 5.4 Status yangilash

**Jarayon:**

1. Manager `🔄 Status yangilash` → Cargo ID kiritadi
2. Bot joriy statusni ko'rsatadi
3. Yangi statusni tanlash uchun inline tugmalar:
    ```
    [🕐 Kutilmoqda] [🚚 Yo'lda]
    [📦 Yetib keldi] [✅ Tayyor]
    [🎉 Topshirildi]
    ```
4. Manager yangi statusni tanlaydi
5. Baza yangilanadi
6. **Client ga avtomatik xabarnoma yuboriladi** (8-bo'lim)

### 5.5 Yuklarni ko'rish va qidirish

Manager quyidagi filtrlar bo'yicha yuklarni ko'rishi mumkin:

- Barcha yuklar (sahifalab — 10 tadan)
- Status bo'yicha filtrlash
- Telefon raqam bo'yicha qidirish
- Cargo ID bo'yicha qidirish

### 5.6 Excel eksport

**Funksiya:** Manager `📥 Excel eksport` tugmasini bosadi → tizim `.xlsx` fayl generatsiya qiladi va botdan yuboradi.

**Excel fayl tuzilmasi:**

| Cargo ID | Mijoz ismi | Telefon | Yuk nomi | Kilo | Cargo kilo | Narxi | Valyuta | Status | Yaratilgan |
| -------- | ---------- | ------- | -------- | ---- | ---------- | ----- | ------- | ------ | ---------- |
| 48392    | ...        | ...     | ...      | ...  | ...        | ...   | ...     | ...    | ...        |

**Qo'shimcha xususiyatlar:**

- Sarlavha qatori qalin va rangli
- Ustun kengliklari avtomatik sozlanadi
- Fayl nomi: `cargo_export_YYYY-MM-DD.xlsx`
- Eksport vaqtida filtrlash imkoniyati: barcha yuklar / faqat aktiv

---

## 6. Client paneli — Funksional talablar

### 6.1 Client asosiy menyusi

```
📦 Client Panel
├── 🆔 Mening Cargo ID im
├── 🔍 Yukimni kuzatish
├── 🛍️ Bizning guruhlar
└── 📞 Bog'lanish
```

### 6.2 Birinchi kirish (onboarding)

1. Client `/start` bosadi
2. Til tanlanadi (O'zbek 🇺🇿 / Русский 🇷🇺 / Türkçe 🇹🇷)
3. Telefon raqamini ulashish so'raladi (Telegram `request_contact` tugmasi)
4. Asosiy menyu ko'rsatiladi

### 6.3 Mening Cargo ID im

- Client `🆔 Mening Cargo ID im` tugmasini bosadi
- Tizim clientning telefon raqami bilan bog'liq barcha Cargo ID larini ko'rsatadi
- Har bir ID yonida joriy holati va yaratilgan sanasi ko'rinadi

**Ko'rinish namunasi:**

```
📦 Sizning yuklaringiz:

1️⃣  Cargo ID: 48392
    📦 Holat: 🚚 Yo'lda
    📅 Yaratilgan: 12.05.2025

2️⃣  Cargo ID: 73015
    📦 Holat: ✅ Tayyor
    📅 Yaratilgan: 03.05.2025
```

### 6.4 Yukni kuzatish

1. Client `🔍 Yukimni kuzatish` → Cargo ID kiritadi
2. Tizim tekshiradi:
    - ID mavjudmi?
    - ID shu clientga tegishlimi? (telefon raqami orqali)
3. **Moslik bo'lsa** — to'liq ma'lumot ko'rsatiladi:

```
📦 Yuk ma'lumoti
━━━━━━━━━━━━━━━━━
🆔 Cargo ID:     48392
📋 Yuk:          Kiyim-kechak
⚖️  Kilosi:       25 kg
📦 Cargo kilosi: 120 kg
💰 Narxi:        $450
📌 Holat:        🚚 Yo'lda
📝 Izoh:         Ehtiyotkorlik bilan
📅 Yaratilgan:   12.05.2025
━━━━━━━━━━━━━━━━━
[🖼️ Rasmni ko'rish]
```

4. **Moslik bo'lmasa** — "Bu Cargo ID siz bilan bog'liq emas" xabar

### 6.5 Bizning guruhlar

Client `🛍️ Bizning guruhlar` tugmasini bosadi va guruhlar ro'yxati inline tugmalar ko'rinishida chiqadi:

```
[👔 Erkaklar kiyimi]
[👗 Ayollar kiyimi]
[🧒 Bolalar kiyimi]
[👟 Oyoq kiyimlar]
```

Har bir tugma bosilganda Telegram guruh havolasi yuboriladi.

### 6.6 Bog'lanish

`📞 Bog'lanish` tugmasi bosilganda:

```
📍 Manzil:
   [manzil matni]

📞 Telefon raqamlar:
   +998 XX XXX-XX-XX
   +998 XX XXX-XX-XX

✈️ Telegram:
   @username

⏰ Ish vaqti:
   Du-Sha: 09:00 - 18:00
```

---

## 7. Bot scenariylari (Flows)

### 7.1 Yangi client onboarding

```
/start
  └─► Til tanlash (uz / ru / tr)
        └─► Telefon raqam so'rash
              ├─► Mavjud client → Asosiy menyu
              └─► Yangi client → Ro'yxatga olish → Asosiy menyu
```

### 7.2 Manager: Cargo ID yaratib yuk biriktirish

```
Manager → ➕ Yangi Cargo ID yaratish
  └─► Telefon raqam kiritish
        ├─► Client topildi → ID yaratiladi → [48392] ✅
        └─► Client topilmadi → Yangi yozuv → ID yaratiladi → [48392] ✅

Manager → 📦 Yuk biriktirish
  └─► Cargo ID kiritish
        └─► Yuk nomi → Kilo → Cargo kilo → Narxi → Valyuta → Rasm → Izoh
              └─► Preview → Tasdiqlash → ✅ Saqlandi
```

### 7.3 Status yangilash va xabarnoma

```
Manager → 🔄 Status yangilash → Cargo ID → Yangi status
  └─► Baza yangilanadi
        └─► Client ga push xabarnoma ──► Client Telegram ga xabar oladi
```

### 7.4 Client: Yukni kuzatish

```
Client → 🔍 Yukimni kuzatish → Cargo ID kiritish
  ├─► ID mavjud + client mos → To'liq ma'lumot ko'rsatiladi
  ├─► ID mavjud + client mos emas → ⛔ Ruxsat yo'q xabari
  └─► ID mavjud emas → ❌ Topilmadi xabari
```

---

## 8. Xabarnoma tizimi

### 8.1 Status o'zgarganda xabarnoma

Manager statusni o'zgartirishi bilanoq, tizim clientning Telegram ID si ga avtomatik xabar yuboradi.

**Xabar formati (O'zbekcha):**

```
📦 Yukingiz holati yangilandi!

🆔 Cargo ID: 48392
📋 Yuk: Kiyim-kechak
🔄 Yangi holat: ✅ Tayyor

Yukingizni olib kelishingiz mumkin.
```

### 8.2 Xabarnoma yuborib bo'lmaydigan holatlar

- Client botni bloklagan bo'lsa → xato loglarga yoziladi, davom etadi
- Client Telegram ID si bazada yo'q bo'lsa → xabarnoma o'tkazib yuboriladi

---

## 9. Ko'p tilli qo'llab-quvvatlash (i18n)

### 9.1 Qo'llab-quvvatlanadigan tillar

| Til     | Kodi | Bayroq |
| ------- | ---- | ------ |
| O'zbek  | `uz` | 🇺🇿     |
| Ruscha  | `ru` | 🇷🇺     |
| Turkcha | `tr` | 🇹🇷     |

### 9.2 Amalga oshirish

- Barcha bot xabarlari `locales/uz.json`, `locales/ru.json`, `locales/tr.json` fayllarida saqlanadi
- Client tanlagan til `clients.language` ustunida saqlanadi
- Client har qanday vaqt tilni o'zgartirishi mumkin → Sozlamalar menyusidan
- Xabarnomalar ham client tanlagan tilda yuboriladi

### 9.3 Til o'zgartirish

```
Asosiy menyu → ⚙️ Sozlamalar → 🌐 Tilni o'zgartirish
  └─► [🇺🇿 O'zbek] [🇷🇺 Русский] [🇹🇷 Türkçe]
```

---

## 10. Acceptance Criteria

### AC-01 — Cargo ID yaratish

| #   | Shart                                           | Kutilgan natija                               |
| --- | ----------------------------------------------- | --------------------------------------------- |
| 1   | Manager mavjud telefon raqam kiritsa            | Mavjud clientga yangi 5 xonali ID yaratiladi  |
| 2   | Manager yangi telefon raqam kiritsa             | Yangi client yozuvi va 5 xonali ID yaratiladi |
| 3   | ID avval bazada mavjud bo'lmasligi              | Tizim unikal ID kafolatlaydi (collision yo'q) |
| 4   | Yaratilgan ID faqat raqamlardan iborat bo'lishi | `[0-9]{5}` formatiga mos keladi               |

### AC-02 — Yuk ma'lumotlari

| #   | Shart                                                                | Kutilgan natija                                                            |
| --- | -------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 1   | Faqat "Yuk nimaligi" kiritib, qolganlarini o'tkazib yuborilsa        | Yuk bazaga saqlanadi, bo'sh maydonlar `NULL`                               |
| 2   | "Yuk nimaligi" bo'sh qoldirilsa yoki o'tkazib yuborilmoqchi bo'linsa | Bot xato xabar beradi va qayta so'raydi                                    |
| 3   | Ixtiyoriy raqamli maydonlarga manfiy son kiritilsa                   | Bot xato xabar beradi, qayta so'raydi                                      |
| 4   | Narx kiritilgan bo'lsa                                               | Valyuta tanlash so'raladi; narx o'tkazib yuborilsa valyuta ham o'tkaziladi |
| 5   | Barcha maydonlar to'liq kiritilsa                                    | Preview ko'rsatiladi, tasdiqlangach saqlanadi                              |

### AC-03 — Status yangilash

| #   | Shart                         | Kutilgan natija                             |
| --- | ----------------------------- | ------------------------------------------- |
| 1   | Manager statusni o'zgartirsa  | Baza 5 soniyadan kam vaqtda yangilanadi     |
| 2   | Status yangilansa             | Client ga avtomatik xabarnoma yuboriladi    |
| 3   | Client botni bloklagan bo'lsa | Xato yashiriladi, bot ishlashda davom etadi |

### AC-04 — Client: Cargo ID ko'rish

| #   | Shart                                | Kutilgan natija                                          |
| --- | ------------------------------------ | -------------------------------------------------------- |
| 1   | Client `🆔 Mening Cargo ID im` bossa | Unga tegishli barcha Cargo ID lar va holatlari ko'rinadi |
| 2   | Clientning hech qanday yuki bo'lmasa | "Hozircha yukingiz yo'q" xabari ko'rinadi                |

### AC-05 — Client: Yukni kuzatish

| #   | Shart                                     | Kutilgan natija                       |
| --- | ----------------------------------------- | ------------------------------------- |
| 1   | Client o'ziga tegishli Cargo ID kiritsa   | To'liq yuk ma'lumoti ko'rsatiladi     |
| 2   | Client boshqa clientning Cargo ID kiritsa | "Bu ID siz bilan bog'liq emas" xabari |
| 3   | Mavjud bo'lmagan ID kiritilsa             | "Topilmadi" xabari                    |

### AC-06 — Excel eksport

| #   | Shart                                                  | Kutilgan natija                                |
| --- | ------------------------------------------------------ | ---------------------------------------------- |
| 1   | Manager eksport bossa                                  | .xlsx fayl 10 soniyadan kam vaqtda yuboriladi  |
| 2   | Eksport fayli barcha yuk yozuvlarini o'z ichiga olishi | Hech qanday yozuv tushib qolmaydi              |
| 3   | Rasm ustunida                                          | Telegram file_id yoziladi (rasm chiqarilmaydi) |

### AC-07 — Autentifikatsiya

| #   | Shart                                           | Kutilgan natija                                   |
| --- | ----------------------------------------------- | ------------------------------------------------- |
| 1   | Whitelist dagi manager kirsa                    | Manager menyusi ko'rsatiladi                      |
| 2   | Oddiy foydalanuvchi manager buyrug'ini ishlatsa | "Ruxsat yo'q" xabari, client menyusi ko'rsatiladi |
| 3   | Client telefonsiz kirsa                         | Telefon raqami majburiy so'raladi                 |

### AC-08 — Ko'p tilli qo'llab-quvvatlash

| #   | Shart                    | Kutilgan natija                            |
| --- | ------------------------ | ------------------------------------------ |
| 1   | Client O'zbekcha tanlasa | Barcha interfeys va xabarnomalar O'zbekcha |
| 2   | Client tilni o'zgartirsa | Keyingi barcha xabarlar yangi tilda        |
| 3   | Status xabarnomasi       | Clientning tanlagan tilida yuboriladi      |

---

## 11. Non-funksional talablar

### 11.1 Ishlash samaradorligi

| Ko'rsatkich                   | Talab                         |
| ----------------------------- | ----------------------------- |
| Bot javob vaqti               | ≤ 2 soniya (oddiy so'rovlar)  |
| Excel generatsiya             | ≤ 10 soniya (1000 yozuvgacha) |
| Ma'lumotlar bazasi so'rovlari | ≤ 500ms                       |
| Bir vaqtda foydalanuvchilar   | ≥ 100 simultaneous            |

### 11.2 Ishonchlilik

- Bot 24/7 ishlashi kerak
- Xatolar loglarda saqlanishi kerak (`logging` moduli)
- Bekor bo'lgan so'rovlar qayta ishlanishi kerak (retry mechanism)
- Database connection pool: min 5, max 20

### 11.3 Xavfsizlik

- Manager ID lari faqat `.env` da saqlanadi, kodda hardcode qilinmaydi
- Bot token `.env` da saqlanadi
- SQL injection — SQLAlchemy ORM orqali oldini olinadi
- Client faqat o'zining yuklarini ko'ra oladi

### 11.4 Kengayish imkoniyati

- Guruhlar bazada saqlanadi va manager qo'shishi/o'chirishi mumkin
- Kompaniya ma'lumotlari bazada saqlanadi va yangilanishi mumkin
- Yangi til qo'shish — yangi JSON fayl qo'shish va bot ro'yxatga olish bilan amalga oshiriladi

---

## 12. Deployment

### 12.1 Infratuzilma

```
VPS (Linux Ubuntu 22.04)
├── Docker Engine
├── Docker Compose
│   ├── cargo_bot (Python container)
│   └── postgres (PostgreSQL 15)
└── Systemd (auto-restart)
```

### 12.2 Muhit o'zgaruvchilari (`.env`)

```env
# Telegram
BOT_TOKEN=your_bot_token_here
MANAGER_IDS=123456789,987654321

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=cargo_db
DB_USER=cargo_user
DB_PASSWORD=strong_password_here

# App
LOG_LEVEL=INFO
```

### 12.3 Ishga tushirish

```bash
# 1. Repozitoriyani clone qilish
git clone https://github.com/company/cargo-bot.git
cd cargo-bot

# 2. .env faylini to'ldirish
cp .env.example .env
nano .env

# 3. Docker Compose bilan ishga tushirish
docker-compose up -d

# 4. Migration
docker exec cargo_bot alembic upgrade head

# 5. Loglarni kuzatish
docker-compose logs -f cargo_bot
```

### 12.4 Bosqichli yetkazib berish (Milestones)

| Bosqich     | Tarkib                                                             | Muddat     |
| ----------- | ------------------------------------------------------------------ | ---------- |
| **MVP**     | Manager panel, Cargo ID yaratish, Yuk biriktirish, Client kuzatish | Sprint 1-2 |
| **Beta**    | Status yangilash, Push notification, Client ID ko'rish             | Sprint 3   |
| **Release** | Excel eksport, Ko'p til, Guruhlar, Bog'lanish                      | Sprint 4   |
| **Polish**  | Test, Bug fix, Deploy                                              | Sprint 5   |

---

## ILOVALAR

### A. Boshlang'ich guruhlar ro'yxati

| Guruh nomi (UZ) | Guruh nomi (RU) | Guruh nomi (TR) | Emoji |
| --------------- | --------------- | --------------- | ----- |
| Erkaklar kiyimi | Мужская одежда  | Erkek giyim     | 👔    |
| Ayollar kiyimi  | Женская одежда  | Kadın giyim     | 👗    |
| Bolalar kiyimi  | Детская одежда  | Çocuk giyim     | 🧒    |
| Oyoq kiyimlar   | Обувь           | Ayakkabılar     | 👟    |

### B. Xato xabarlari ro'yxati

| Kod             | O'zbekcha                          | Ruscha                         | Turkcha                 |
| --------------- | ---------------------------------- | ------------------------------ | ----------------------- |
| ERR_NOT_FOUND   | ❌ Cargo ID topilmadi              | ❌ Cargo ID не найден          | ❌ Cargo ID bulunamadı  |
| ERR_NO_ACCESS   | ⛔ Bu ID siz bilan bog'liq emas    | ⛔ Этот ID не принадлежит вам  | ⛔ Bu ID size ait değil |
| ERR_INVALID_NUM | ⚠️ Faqat musbat son kiriting       | ⚠️ Введите положительное число | ⚠️ Pozitif sayı girin   |
| ERR_NO_PERM     | 🚫 Sizda bu amal uchun ruxsat yo'q | 🚫 Нет доступа                 | 🚫 Erişim yok           |

---

_Hujjat versiyasi: 1.0 | Oxirgi yangilangan: 2025_
