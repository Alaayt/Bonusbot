# دليل النشر

## المتطلبات
- Python 3.11+ (تم تطوير المشروع واختباره فعليًا على Python 3.14)
- PostgreSQL (إنتاج) أو SQLite (تطوير/تجربة سريعة)
- Redis (اختياري حاليًا - محجوز لاستخدامات مستقبلية مثل تخزين مؤقت لجلسات RAG)
- Bot Token من [@BotFather](https://t.me/BotFather)
- مفتاح OpenAI API من [platform.openai.com](https://platform.openai.com/api-keys)

## النشر عبر Docker (موصى به)

```bash
cp .env.example .env
# املأ كل القيم في .env
docker compose up --build -d
docker compose logs -f bot
```

`docker-compose.yml` يشغّل: البوت + Redis + PostgreSQL معًا. البيانات (`data/promotions`, `data/raw_sources`) تُركَّب كـ volume فتبقى محفوظة بين إعادة التشغيل.

## النشر اليدوي (VPS)

```bash
git clone <repo>
cd Bonusbot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # واملأه

python -m alembic upgrade head
python -m app.main
```

للتشغيل الدائم، استخدم `systemd` أو `supervisor` أو `pm2` (عبر `pm2 start "python -m app.main" --name bonusbot`).

## وضع Webhook مقابل Polling

المشروع مهيأ افتراضيًا على **polling** (`dp.start_polling(bot)` في `app/main.py`) لأنه أبسط للتشغيل الأولي ولا يحتاج شهادة SSL أو دومين عام. للتحويل لـ Webhook في الإنتاج:
1. اضبط `WEBHOOK_URL` و`WEBHOOK_SECRET` في `.env`.
2. استبدل استدعاء `dp.start_polling(bot)` في `app/main.py` بإعداد خادم aiohttp مع `SimpleRequestHandler` من aiogram (نمط قياسي موثّق في [توثيق aiogram الرسمي](https://docs.aiogram.dev)).

## قاعدة البيانات

- التطوير: `DATABASE_URL=sqlite+aiosqlite:///./data/bonusbot.db` (تلقائي - `init_db()` ينشئ الجداول عند أول تشغيل).
- الإنتاج: `DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/bonusbot` ثم:
  ```bash
  python -m alembic upgrade head
  ```
- Migration أولية جاهزة في `app/database/migrations/versions/`.

## متغيرات البيئة الحرجة قبل التشغيل الفعلي

| المتغير | الأهمية |
|---|---|
| `TELEGRAM_BOT_TOKEN` | إلزامي - البوت يرفض التشغيل بدونه |
| `OPENAI_API_KEY` | إلزامي لأي رد نصي حر (المحادثات الطبيعية خارج القوائم) |
| `ADMIN_IDS` | إلزامي لتفعيل لوحة الإدارة (قائمة Telegram ID مفصولة بفواصل) |
| `AFFILIATE_REGISTRATION_URL` | بدونه، البوت يعرض البروموكود فقط ويطلب من المستخدم مراجعة المدير للرابط |
| `APP_DOWNLOAD_URL` | رابط تحميل التطبيق المعروض للمستخدم |
| `PROMO_CODE` | افتراضيًا `VIP10IQ` - غيّره فقط إذا تغيّر البروموكود الرسمي |

## المراقبة بعد النشر

- `/admin_stats` و`/admin_top_offers` من داخل تيليجرام لأي معرّف في `ADMIN_IDS`.
- سجلات التطبيق تُطبع على stdout (`app/common/logging.py`) - وجّهها لأي نظام مراقبة سجلات تفضّله (journald، Docker logs، إلخ).
