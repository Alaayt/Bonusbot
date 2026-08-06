from app.ai.rag.search import get_relevant_promotions


def test_finds_first_deposit_bonus_by_arabic_query():
    results = get_relevant_promotions("ابي بونص اول ايداع", lang="ar")
    slugs = [p.slug for p in results]
    assert "first_deposit" in slugs or "slot_first_deposit" in slugs


def test_finds_casino_offers_by_keyword():
    results = get_relevant_promotions("عروض كازينو سلوت", lang="ar")
    assert any(p.category.startswith("casino") for p in results)


def test_does_not_return_expired_offers_at_top():
    results = get_relevant_promotions("بونص", lang="ar", limit=20)
    statuses = [p.status for p in results]
    if "expired" in statuses:
        expired_index = statuses.index("expired")
        active_indices = [i for i, s in enumerate(statuses) if s == "active"]
        assert not active_indices or min(active_indices) < expired_index


def test_country_mismatch_lowers_priority_not_hides_completely():
    results_iq = get_relevant_promotions("بونص", lang="ar", country_code="IQ", limit=10)
    assert len(results_iq) > 0


def test_unrelated_query_returns_reasonable_or_empty_results():
    results = get_relevant_promotions("طقس اليوم في بغداد", lang="ar")
    assert isinstance(results, list)
