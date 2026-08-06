"""
اختبار انحداري (regression) لخطأ حقيقي وقع فعليًا في الإنتاج: كل أزرار القائمة الرئيسية
كانت تُرجع "العرض غير موجود" لأن CATEGORY_MAP في app/bot/handlers/offers.py كان يستخدم
startswith() بينما فئات العروض بصيغة "<domain>_<type>" (مثل sports_deposit_bonus)، فلا شيء
يبدأ فعليًا بكلمة مثل "deposit_bonus". هذا الاختبار يضمن أن كل زر من أزرار القائمة الرئيسية
الثمانية المرتبطة بفئة يُرجع نتيجة واحدة على الأقل من قاعدة المعرفة الحالية.
"""

from app.bot.handlers.offers import CATEGORY_MAP
from app.promotions.services.promotion_store import get_by_category_keywords


def test_every_menu_category_button_returns_at_least_one_offer():
    for cat_key, keywords in CATEGORY_MAP.items():
        results = get_by_category_keywords(keywords)
        assert results, f"زر الفئة '{cat_key}' لا يُرجع أي عرض - تحقق من مطابقة الكلمات المفتاحية {keywords}"


def test_category_keywords_use_substring_matching_not_prefix_only():
    # "sports_deposit_bonus" لا يبدأ بـ "deposit_bonus" لكنه يحتوي عليها - هذا بالضبط ما كان يكسر الزر
    results = get_by_category_keywords(["deposit_bonus"])
    slugs = {p.slug for p in results}
    assert "first_deposit" in slugs
