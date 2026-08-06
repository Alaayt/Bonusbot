"""
مهمة مجدولة دورية لاكتشاف تغييرات صفحات العروض.

الخطوات:
1. زيارة كل رابط عرض (عبر web_extractor - يفشل بأمان عند الحجب الجغرافي دون تعطيل النظام).
2. مقارنة النص الجديد بالنص المخزّن في data/raw_sources/<slug>.txt.
3. إن اختلف النص، إنشاء PendingUpdate بدل نشره تلقائيًا (يحتاج موافقة المشرف عبر /admin_pending).
4. تعطيل العروض تلقائيًا التي تجاوز end_at المؤكد تاريخ اليوم (status الفعلي، وليس حذفها من القاعدة).
5. تسجيل Audit Log لكل تغيير.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database.engine import async_session_maker
from app.database.repositories.promotion_meta_repository import create_pending_update, log_audit
from app.promotions.parsers.web_extractor import fetch_page_text
from app.promotions.services.promotion_store import DATA_DIR, get_all_promotions, reload_promotions

RAW_SOURCES_DIR = Path(__file__).resolve().parents[2] / "data" / "raw_sources"


async def check_for_offer_updates() -> None:
    async with async_session_maker() as session:
        for promo in get_all_promotions():
            if not promo.source_url:
                continue

            new_text = await fetch_page_text(promo.source_url)
            if new_text is None:
                continue  # حجب/فشل الوصول - لا نفعل شيئًا، هذا متوقع في البيئات المحجوبة جغرافيًا

            raw_file = RAW_SOURCES_DIR / f"{promo.slug}.txt"
            old_text = raw_file.read_text(encoding="utf-8") if raw_file.exists() else None

            if old_text is not None and _normalize(old_text) == _normalize(new_text):
                continue  # لا تغيير

            await create_pending_update(session, slug=promo.slug, new_text=new_text, source="scheduler", old_text=old_text)
            await log_audit(session, None, "detected_offer_change", promo.slug, "تم اكتشاف تغيير محتمل - بانتظار مراجعة المشرف")


async def expire_outdated_offers() -> None:
    """تعطيل العروض تلقائيًا فقط عندما يكون end_at مؤكدًا (وليس null) وقد مضى تاريخه فعليًا."""
    today = datetime.now(timezone.utc)
    changed = False

    for promo_file in DATA_DIR.glob("*.json"):
        raw = json.loads(promo_file.read_text(encoding="utf-8"))
        end_at = raw.get("end_at")
        if not end_at or raw.get("status") == "expired":
            continue
        try:
            end_dt = datetime.fromisoformat(end_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        if end_dt < today:
            raw["status"] = "expired"
            promo_file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
            changed = True

    if changed:
        reload_promotions()


def _normalize(text: str) -> str:
    return " ".join(text.split()).lower()


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(check_for_offer_updates, "interval", hours=12, id="check_for_offer_updates")
    scheduler.add_job(expire_outdated_offers, "interval", hours=1, id="expire_outdated_offers")
    scheduler.start()
    return scheduler
