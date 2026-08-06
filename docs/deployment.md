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

`docker-compose.yml` يشغّل: البوت + Redis + PostgreSQL معًا. `./data:/app/data` هنا هو **bind mount من مجلد المشروع نفسه على الجهاز المضيف** (وليس Volume فارغ) - يعمل بأمان لأن `./data` على القرص فعليًا يحتوي على `promotions/` و`raw_sources/` من البداية.

## ⚠️ تحذير حرج: Volumes على منصات الاستضافة السحابية (Railway/Render/Fly.io...)

هذا خطأ شائع جدًا ويُسقط قاعدة معرفة العروض بالكامل بصمت (بدون أي رسالة خطأ واضحة، فقط `/admin_stats` يظهر "عدد العروض: 0"):

**المشكلة:** أي Volume تُنشئه حديثًا على منصات مثل Railway يبدأ **فارغًا تمامًا**. لو ركّبته على مسار `/app/data` (نفس المسار اللي فيه `data/promotions/` و`data/raw_sources/` المُدمجة داخل صورة Docker من خطوة `COPY . .` في `Dockerfile`)، فإن Railway "يغطي" محتوى الصورة بالفراغ - فيختفي كل ملفات JSON للعروض من منظور التطبيق وقت التشغيل، رغم وجودها في الكود على GitHub.

**الحل الصحيح:** ركّب الـ Volume على مسار **فرعي أضيق** مخصص فقط لملف قاعدة البيانات (الشيء الوحيد اللي يحتاج فعليًا يبقى Persistent بين عمليات إعادة النشر)، وليس على `data/` كاملة:

1. **Mount Path** في إعدادات الـ Volume:
   ```
   /app/data/db
   ```
   (وليس `/app/data`)

2. **متغير البيئة** `DATABASE_URL`:
   ```
   DATABASE_URL=sqlite+aiosqlite:///./data/db/bonusbot.db
   ```

بهذا الشكل: `data/promotions` و`data/raw_sources` يبقيان من الصورة (يتحدّثان فقط عبر `git push` جديد)، بينما `data/db/bonusbot.db` (المستخدمون، المحادثات، التنبيهات) يبقى محفوظًا عبر Volume منفصل لا يلمس ملفات العروض.

بديل أنظف للإنتاج: استخدم PostgreSQL بدل SQLite (أضِف Postgres من Railway نفسه واضبط `DATABASE_URL=postgresql+asyncpg://...`) - عندها لا تحتاج أي Volume إطلاقًا، ويختفي هذا الخطر نهائيًا.

بعد أي تعديل، تحقق فورًا عبر `/admin_stats` من داخل تيليجرام: يجب أن يظهر "عدد العروض في قاعدة المعرفة: 29" (أو أكثر لاحقًا). لو ظهر 0، راجع سجلات الإقلاع (Logs) - أضفنا تحذيرًا صريحًا (`_check_promotions_loaded` في `app/main.py`) يظهر في السجلات فورًا عند هذه المشكلة تحديدًا.

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

## واجهة البوت: زر القائمة، الأوامر، والمعاينة الجميلة عند مشاركة الرابط

عند إقلاع البوت، `app/bot/setup_profile.py::setup_bot_profile()` يضبط تلقائيًا (عبر Bot API، بلا تدخل يدوي):
- **زر القائمة الدائم** بجانب حقل الكتابة (Menu Button) → يفتح قائمة أوامر جاهزة.
- **قائمة الأوامر** (`/menu`, `/language`, `/help`, `/manager`, `/responsible`, `/stop_marketing`) بثلاث لغات حسب لغة عميل تيليجرام لكل مستخدم.
- **الوصف القصير** (`setMyShortDescription`) - هذا بالضبط ما يظهر في معاينة الرابط الجميلة عند مشاركة `t.me/YourBotUsername` (تحت الاسم والصورة).
- **الوصف الكامل** (`setMyDescription`) - يظهر في شاشة الترحيب الفارغة قبل أن يرسل المستخدم أول رسالة (مع زر "ابدأ" الظاهر تلقائيًا من تيليجرام نفسه لأي بوت).

### الخطوة اليدوية الوحيدة المتبقية: صورة البوت الشخصية
لا يوجد endpoint في Bot API يسمح للبوت بتعيين صورته الشخصية ذاتيًا - هذه فقط عبر [@BotFather](https://t.me/BotFather):
```
/mybots → اختر البوت → Edit Bot → Edit Botpic
```
ارفع صورة مربعة واضحة (لوجو 1xBet أو تصميم يعكس هوية "مستشار البونصات") - هذا يكمّل شكل الرابط الجميل عند المشاركة (الاسم + الوصف القصير + الصورة معًا).
