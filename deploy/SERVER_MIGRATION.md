# Botni yangi serverga ko'chirish (eski data bilan)

Eski server: PostgreSQL 15.17, `cargo_db`. Yangi server: `Docker/docker-compose.yml`
(postgres:15-alpine + bot).

## 0. Dump haqida

Yuklab olingan `aliway_pg_full_<sana>.sql.gz` — bu **`pg_dumpall` cluster dump**:
ichida rollar (`postgres`, `cargo_user` parol hash'lari bilan), `template1`,
`cargo_db` va `postgres` DB'lari bor. Uni to'g'ridan-to'g'ri yangi konteynerga
quyib bo'lmaydi, chunki:

- Docker postgres image init paytida `POSTGRES_USER` va `POSTGRES_DB` ni allaqachon
  yaratib qo'yadi → `CREATE ROLE ...` / `CREATE DATABASE cargo_db` xato beradi;
- dump'da `OWNER TO postgres` va `GRANT ... TO cargo_user` bor — yangi serverda bu
  rollarning ikkalasi ham bo'lmasligi mumkin;
- dump'dagi `\restrict` / `\unrestrict` meta-buyruqlari eski psql client'da xato beradi.

Shu sabab faqat `cargo_db` qismi ajratib olinib, owner/GRANT satrlari olib tashlangan
**owner-neutral** fayl tayyorlangan: `cargo_db_restore.sql.gz`.
Uni kim restore qilsa, jadvallar egasi o'sha bo'ladi — ya'ni `postgres` ham,
`cargo_user` ham bo'laveradi.

Shu faylni o'zingiz ham qayta yasay olasiz:

```bash
gunzip -c aliway_pg_full_2026-07-30.sql.gz | awk '
  index($0,"\\connect cargo_db")==1 {on=1; next}
  $0=="-- Database \"postgres\" dump" {on=0}
  on {
    if (index($0,"\\restrict")==1 || index($0,"\\unrestrict")==1 || index($0,"\\connect")==1) next
    if (index($0,"OWNER TO ")>0 || index($0,"GRANT ")==1 || index($0,"REVOKE ")==1) next
    print
  }' | gzip -9 > cargo_db_restore.sql.gz
```

Dump ichidagi ma'lumot (tekshirish uchun mo'ljal):

| Jadval | Satr |
|---|---|
| clients | 412 |
| shipments | 11 |
| groups | 9 |
| group_categories | 3 |
| company_info | 1 |
| alembic_version | 1 (`add_grp_categories`) |

`alembic_version = add_grp_categories` — bu koddagi oxirgi migration (head).
Ya'ni restore'dan keyin qo'shimcha migration kerak emas; bot start'idagi
`alembic upgrade head` hech narsa qilmaydi.

## 1. Cutover'dan oldin

1. **Eski botni to'xtating.** Ikkita bot bir token bilan polling qilsa Telegram
   409 Conflict beradi va xabarlar yo'qoladi:
   ```bash
   # eski serverda
   docker compose -f Docker/docker-compose.yml stop bot
   ```
2. **Yangi (final) dump oling.** 2026-07-30 dagi dump'dan keyin mijoz qo'shilgan
   bo'lsa, u yo'qoladi. Botni to'xtatgandan keyin qayta dump qiling:
   ```bash
   # eski serverda, faqat cargo_db (tavsiya etiladi)
   docker compose exec -T postgres pg_dump -U postgres -d cargo_db --no-owner --no-acl \
     | gzip -9 > cargo_db_$(date +%F).sql.gz
   ```
   `--no-owner --no-acl` tufayli yuqoridagi awk tozalash umuman kerak bo'lmaydi.
3. Faylni yangi serverga tashlang: `scp cargo_db_restore.sql.gz user@yangi-server:~/`

## 2. Yangi serverni tayyorlash

```bash
git clone <repo> AliwayBot && cd AliwayBot
```

`.env` faylini qo'lda yarating (u git'da yo'q — `.gitignore` da). Eski serverdagi
`.env` dan ko'chiring, faqat quyidagilarga e'tibor bering:

```ini
BOT_TOKEN=<eski token>
MANAGER_IDS=<eski ro'yxat>

DB_HOST=postgres          # docker ichida — postgres, localhost EMAS
DB_PORT=5432              # host'ga chiqariladigan port; band bo'lsa boshqasini bering
DB_NAME=cargo_db
DB_USER=postgres          # eski serverdagi bilan bir xil bo'lsin
DB_PASSWORD=<parol>
```

> ⚠️ **Muhim:** `docker-compose.yml` `Docker/` papkasida, lekin `${DB_USER}` kabi
> o'zgaruvchilarni compose **ishga tushirilgan papkadagi `.env`** dan oladi.
> `cd Docker && docker compose up` qilsangiz `.env` topilmaydi va compose'dagi
> `environment:` bloki `env_file` qiymatlarini bosib ketadi: `BOT_TOKEN` **bo'sh**
> bo'ladi (bot ishga tushmaydi), DB esa default `cargo_user` / `postgresql`
> (kuchsiz parol) bilan yaratiladi.
> Har doim repo ildizidan ishga tushiring:
>
> ```bash
> docker compose --env-file .env -f Docker/docker-compose.yml <buyruq>
> ```

Qulaylik uchun alias:

```bash
alias dc='docker compose --env-file .env -f Docker/docker-compose.yml'
```

## 3. Faqat bazani ko'tarish

```bash
dc up -d postgres
dc ps          # postgres "healthy" bo'lguncha kuting
```

`postgres_data` volume bo'sh bo'lishi kerak. Agar avval ishga tushirgan bo'lsangiz
(masalan `seed.py` ishlagan bo'lsa) — bazani tozalang:

```bash
dc down -v            # DIQQAT: volume o'chadi, faqat yangi serverda qiling
dc up -d postgres
```

Yoki volume'ni o'chirmasdan faqat schema'ni tozalash:

```bash
dc exec -T postgres psql -U postgres -d cargo_db \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

## 4. Datani tiklash

```bash
gunzip -c ~/cargo_db_restore.sql.gz \
  | dc exec -T postgres psql -v ON_ERROR_STOP=1 -1 -U postgres -d cargo_db
```

- `ON_ERROR_STOP=1` — birinchi xatoda to'xtaydi (jimgina yarim restore bo'lib qolmasin);
- `-1` — hammasi bitta tranzaksiyada, xato bo'lsa hech narsa yozilmaydi.

`-U postgres` o'rniga `.env` dagi `DB_USER` ni yozing.

## 5. Tekshirish

```bash
dc exec -T postgres psql -U postgres -d cargo_db -c "
  SELECT 'clients', count(*) FROM clients
  UNION ALL SELECT 'shipments', count(*) FROM shipments
  UNION ALL SELECT 'groups', count(*) FROM groups
  UNION ALL SELECT 'group_categories', count(*) FROM group_categories
  UNION ALL SELECT 'company_info', count(*) FROM company_info;
  SELECT * FROM alembic_version;"
```

Sequence'lar dump'da `setval` bilan tiklanadi (clients=412, shipments=11, ...),
lekin ishonch uchun tekshiring — aks holda yangi yozuvda `duplicate key` chiqadi:

```bash
dc exec -T postgres psql -U postgres -d cargo_db -c "
  SELECT last_value FROM clients_id_seq;
  SELECT max(id) FROM clients;"
```

## 6. Botni ishga tushirish

```bash
dc up -d --build bot
dc logs -f bot
```

Log'da ko'rinishi kerak: `Running database migrations...` → alembic hech narsa
qilmaydi (allaqachon `add_grp_categories`), keyin `Bot ishga tushmoqda...`.

Telegramda tekshiring:
- eski mijoz `/start` bosganda qayta ro'yxatdan o'tishni so'ramasligi kerak
  (telegram_id bazada bor);
- manager panelida mijozlar ro'yxati va yuklar ko'rinishi kerak;
- `/track` bilan mavjud cargo_id qidirib ko'ring.

## 7. Cutover'dan keyin

- Eski serverni **darhol o'chirmang** — 1-2 kun zaxira sifatida tursin
  (lekin bot konteyneri o'chiq holatda, token to'qnashmasin).
- Yangi serverda kunlik backup yo'lga qo'ying:
  ```bash
  0 3 * * * cd /home/user/AliwayBot && docker compose --env-file .env -f Docker/docker-compose.yml \
    exec -T postgres pg_dump -U postgres -d cargo_db --no-owner --no-acl \
    | gzip -9 > /home/user/backups/cargo_db_$(date +\%F).sql.gz
  ```

## Tez-tez uchraydigan xatolar

| Xato | Sabab / yechim |
|---|---|
| `password authentication failed for user ...` | volume boshqa parol bilan init bo'lgan (parolni keyin o'zgartirsangiz volume'dagi eskisi qoladi) → `dc down -v` qilib qaytadan |
| Bot log'ida `token is invalid` / bo'sh `BOT_TOKEN` | compose `.env` ni ko'rmayapti → `--env-file .env` bilan repo ildizidan ishga tushiring |
| `role "cargo_user" does not exist` | asl `pg_dumpall` faylini quyyapsiz — tozalangan `cargo_db_restore.sql.gz` dan foydalaning |
| `database "cargo_db" already exists` | asl cluster dump — 0-bo'limga qarang |
| `invalid command \restrict` | psql client eski — tozalangan faylda bu satrlar olib tashlangan |
| `duplicate key value violates unique constraint "clients_pkey"` | sequence tiklanmagan → `SELECT setval('clients_id_seq', (SELECT max(id) FROM clients));` |
| Telegram `409 Conflict: terminated by other getUpdates` | eski server'da bot hali ishlab turibdi |
| `ValidationError: Extra inputs are not permitted (db_pool_size ...)` | `config.py` da bu maydonlar e'lon qilinmagan edi — kodni `git pull` qiling |
| Bot `Unauthorized` / token ishlamayapti | `.env` da qiymat `<...>` burchak qavslari bilan yozilgan — namunadagi qavslarni olib tashlang |
