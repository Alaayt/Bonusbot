from app.bot.handlers.chat import _wants_registration_or_app
from app.bot.keyboards.common import registration_links_keyboard
from app.locales import SUPPORTED_LANGUAGES, t


def test_registration_links_keyboard_uses_real_url_buttons_not_callback():
    kb = registration_links_keyboard("ar", "https://example.com/register", "https://example.com/app")
    buttons = [btn for row in kb.inline_keyboard for btn in row]

    register_btn = next(b for b in buttons if b.url == "https://example.com/register")
    app_btn = next(b for b in buttons if b.url == "https://example.com/app")
    back_btn = next(b for b in buttons if b.callback_data == "menu:main")

    assert register_btn.url is not None
    assert app_btn.url is not None
    assert back_btn.url is None


def test_registration_links_keyboard_omits_missing_links():
    kb = registration_links_keyboard("ar", "", "")
    buttons = [btn for row in kb.inline_keyboard for btn in row]
    assert len(buttons) == 1  # فقط زر العودة للقائمة، بدون أزرار روابط فارغة/مكسورة


def test_wants_registration_or_app_detects_arabic_intent():
    assert _wants_registration_or_app("شلون أسجل حساب جديد؟")
    assert _wants_registration_or_app("وين رابط تحميل التطبيق")


def test_wants_registration_or_app_detects_english_and_french_intent():
    assert _wants_registration_or_app("how do I register a new account")
    assert _wants_registration_or_app("comment télécharger l'application")


def test_wants_registration_or_app_ignores_unrelated_text():
    assert not _wants_registration_or_app("ما هو معامل الرهان لهذا العرض؟")


def test_profile_completion_strings_exist_in_all_languages():
    for lang in SUPPORTED_LANGUAGES:
        assert t(lang, "profile_completion_intro") != "profile_completion_intro"
        assert t(lang, "profile_completion_steps") != "profile_completion_steps"
        assert t(lang, "profile_completion_benefit") != "profile_completion_benefit"
