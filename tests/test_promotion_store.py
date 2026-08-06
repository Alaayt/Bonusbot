from app.promotions.services.promotion_store import get_all_promotions, get_promotion, reload_promotions


def test_loads_all_promotion_files_without_error():
    reload_promotions()
    promos = get_all_promotions()
    # 24 عرضًا أصليًا موثّقًا + chick_point (متعارض) + 4 إضافية (esports_world_cup, jackys_bet, cashback30, lucky_friday)
    # (تم حذف 7 عروض أصلية لم يصل نصها بعد بناءً على طلب المستخدم - راجع docs/link_audit_report.md)
    assert len(promos) >= 29


def test_known_verified_offer_has_expected_fields():
    promo = get_promotion("first_deposit")
    assert promo is not None
    assert promo.verification_status == "verified"
    assert promo.reward["percentage"] == 100
    assert promo.promo_code == "VIP10IQ"
    assert promo.source_url.startswith("https://1xbet.fi")


def test_blocked_offer_has_no_invented_data():
    promo = get_promotion("chick_point")
    assert promo is not None
    assert promo.verification_status == "blocked"
    assert promo.reward == {}
    assert promo.activation_steps == []


def test_conflicting_source_is_flagged_not_merged():
    chick_point = get_promotion("chick_point")
    esports = get_promotion("esports_world_cup_2026")
    assert chick_point is not None and esports is not None
    assert chick_point.verification_status == "blocked"
    assert "تعارض" in chick_point.important_warnings[0]


def test_expired_and_unknown_offers_are_not_presentable():
    from app.promotions.services.promotion_store import get_presentable_promotions

    presentable_slugs = {p.slug for p in get_presentable_promotions()}
    assert "chick_point" not in presentable_slugs
    assert "first_deposit" in presentable_slugs
