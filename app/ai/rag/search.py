"""
محرك بحث دلالي مبسّط (RAG-lite) على قاعدة معرفة العروض.

بدل تحميل كل العروض داخل System Prompt (وهو ما يُمنع صراحة في متطلبات المشروع)،
هذا المحرك يسترجع فقط العروض الأكثر صلة بسؤال المستخدم بناءً على:
  1. تطابق نصي/فازي (rapidfuzz) مع اسم العرض والفئة والكلمات المفتاحية المرادفة.
  2. تصفية حسب حالة العرض (نستبعد blocked وunknown من نتائج البحث العامة).
  3. ترتيب حسب الأولوية: دولة اللاعب > حالة العرض (active قبل scheduled) > درجة التطابق.

لا يعتمد على نموذج تضمين (embeddings) خارجي حتى لا يتطلب مفتاح API إضافي؛
يمكن استبداله لاحقًا بفهرس متجهي (pgvector/FAISS) دون تغيير واجهة get_relevant_promotions().
"""

from rapidfuzz import fuzz

from app.promotions.schemas.promotion import Promotion
from app.promotions.services.promotion_store import get_presentable_promotions

# كلمات مفتاحية مرادفة لكل فئة تساعد على فهم اللهجات العربية والأخطاء الإملائية
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "sports": ["رياضة", "رياضي", "كرة", "مباريات", "sport", "football", "sports", "foot"],
    "casino": ["كازينو", "سلوت", "casino", "slot", "slots"],
    "crypto": ["كريبتو", "عملات رقمية", "بيتكوين", "crypto", "bitcoin", "usdt"],
    "tournament": ["بطولة", "مسابقة", "توورنمنت", "tournament", "tournoi"],
    "freebet": ["فري بت", "رهان مجاني", "freebet", "free bet"],
    "cashback": ["كاش باك", "استرداد", "cashback", "remboursement"],
    "friends": ["أصدقاء", "دعوة", "إحالة", "friends", "referral", "amis"],
    "spins": ["لفات مجانية", "دورات مجانية", "free spins", "spins"],
}


def _keyword_boost(query: str, promo: Promotion) -> int:
    q = query.lower()
    boost = 0
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if cat in promo.category and any(k in q for k in keywords):
            boost += 25
    return boost


def get_relevant_promotions(
    query: str,
    lang: str = "ar",
    country_code: str | None = None,
    limit: int = 5,
    min_score: float = 45.0,
) -> list[Promotion]:
    candidates = get_presentable_promotions()
    scored: list[tuple[float, Promotion]] = []

    for promo in candidates:
        name_text = f"{promo.name('ar')} {promo.name('en')} {promo.name('fr')} {promo.slug} {promo.category}"
        score = fuzz.partial_ratio(query.lower(), name_text.lower())
        score += _keyword_boost(query, promo)

        # ترتيب حسب الأولوية: النشط أولاً
        if promo.status == "active":
            score += 15
        elif promo.status == "scheduled":
            score += 5
        elif promo.status == "expired":
            score -= 40

        # الدولة: إن كانت العروض محصورة بدول معينة ولا تشمل دولة اللاعب، نخفّض الأولوية بدل الحذف
        if country_code and promo.eligible_countries and "ALL" not in promo.eligible_countries:
            if country_code not in promo.eligible_countries:
                score -= 30
        if country_code and country_code in promo.excluded_countries:
            score -= 60

        scored.append((score, promo))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [p for s, p in scored if s >= min_score][:limit]

    if not results and scored:
        # حتى لو لا يوجد تطابق قوي، أعد أفضل نتيجة واحدة إن كانت معقولة (>25) بدل قائمة فارغة تمامًا
        best_score, best_promo = scored[0]
        if best_score >= 25:
            results = [best_promo]

    return results


def get_promotions_by_slugs(slugs: list[str]) -> list[Promotion]:
    from app.promotions.services.promotion_store import get_promotion

    result = []
    for slug in slugs:
        promo = get_promotion(slug)
        if promo:
            result.append(promo)
    return result
