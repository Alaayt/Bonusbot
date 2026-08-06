from app.locales import SUPPORTED_LANGUAGES, t


def test_all_languages_have_main_menu_buttons():
    keys = [
        "btn_first_deposit", "btn_sports", "btn_casino", "btn_crypto", "btn_tournaments",
        "btn_freebets", "btn_cashback", "btn_invite", "btn_find_for_me", "btn_explain_terms",
        "btn_missing_bonus", "btn_register", "btn_manager", "btn_change_language", "btn_responsible_gaming",
    ]
    for lang in SUPPORTED_LANGUAGES:
        for key in keys:
            value = t(lang, key)
            assert value and value != key, f"مفتاح مفقود: {key} في اللغة {lang}"


def test_fallback_to_arabic_for_unknown_language():
    value = t("de", "btn_manager")
    assert value == t("ar", "btn_manager")


def test_format_placeholders_work():
    value = t("ar", "offer_expired", date="2026-01-01")
    assert "2026-01-01" in value


def test_responsible_gaming_text_mentions_stop_marketing_command():
    for lang in SUPPORTED_LANGUAGES:
        assert "/stop_marketing" in t(lang, "responsible_gaming_text")


def test_welcome_message_interpolates_name_and_suggests_example_questions():
    for lang in SUPPORTED_LANGUAGES:
        rendered = t(lang, "welcome_message", name="Sara")
        assert "Sara" in rendered
        assert "{name}" not in rendered
        assert "💬" in rendered  # يحتوي أمثلة أسئلة تشجّع اللاعب يبدأ محادثة طبيعية
