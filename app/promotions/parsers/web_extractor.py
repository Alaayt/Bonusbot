"""
مستخرج صفحات الويب - يُستخدم من المجدول (scheduler) لمحاولة إعادة زيارة روابط العروض دوريًا.

ملاحظة مهمة (راجع docs/link_audit_report.md): وصول هذا المشروع الآلي لموقع 1xbet.fi محجوب
جغرافيًا في بيئة التطوير الحالية. هذا المستخرج مكتوب ليعمل بشكل عام (requests + مُنظّف HTML بسيط)
لأي بيئة إنتاج لا يُحجب فيها الوصول، لكنه *يفشل بأمان* (يعيد None) دون كسر باقي النظام إن حدث حجب،
تمامًا كما طُلب: "إذا منع الموقع الوصول الآلي، لا تحاول تجاوز الحماية."
"""

import re

import httpx


async def fetch_page_text(url: str, timeout: float = 15.0) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
    except Exception:  # noqa: BLE001
        return None

    html = response.text
    if "تم رفض الوصول" in html or "Access denied" in html:
        return None  # حجب جغرافي معروف - لا نحاول تجاوزه

    text = re.sub(r"<script.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None
