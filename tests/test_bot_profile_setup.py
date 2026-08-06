from app.bot.setup_profile import _COMMAND_KEYS
from app.locales import SUPPORTED_LANGUAGES, t


def test_all_command_descriptions_exist_in_every_language():
    for lang in SUPPORTED_LANGUAGES:
        for cmd, desc_key in _COMMAND_KEYS:
            value = t(lang, desc_key)
            assert value != desc_key, f"وصف مفقود للأمر /{cmd} ({desc_key}) في اللغة {lang}"
            assert len(value) <= 256  # حد Telegram الأقصى لوصف الأمر


def test_command_names_are_valid_telegram_slugs():
    for cmd, _ in _COMMAND_KEYS:
        assert cmd.islower()
        assert cmd.replace("_", "").isalnum()
        assert len(cmd) <= 32


def test_bot_descriptions_exist_and_within_limits():
    for lang in SUPPORTED_LANGUAGES:
        short_desc = t(lang, "bot_short_description")
        full_desc = t(lang, "bot_full_description")
        assert short_desc != "bot_short_description"
        assert full_desc != "bot_full_description"
        assert len(short_desc) <= 120  # حد Telegram لـ setMyShortDescription
        assert len(full_desc) <= 512  # حد Telegram لـ setMyDescription
