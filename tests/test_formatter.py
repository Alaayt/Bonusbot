from app.promotions.services.formatter import format_full_details, format_quick_summary
from app.promotions.services.promotion_store import get_promotion


def test_quick_summary_contains_offer_name():
    promo = get_promotion("first_deposit")
    text = format_quick_summary(promo, "ar")
    assert promo.name("ar") in text


def test_full_details_contains_source_url():
    promo = get_promotion("first_deposit")
    text = format_full_details(promo, "ar")
    assert promo.source_url in text


def test_blocked_offer_summary_does_not_invent_numbers():
    promo = get_promotion("chick_point")
    text = format_quick_summary(promo, "ar")
    assert "EUR" not in text
    assert "قيد المراجعة" in text


def test_partial_offer_shows_unverified_warning():
    promo = get_promotion("promo_store")
    text = format_full_details(promo, "ar")
    assert "غير مؤكدة" in text or "unconfirmed" in text.lower()


def test_english_formatting_uses_english_labels():
    promo = get_promotion("first_deposit")
    text = format_full_details(promo, "en")
    assert "Official source" in text
