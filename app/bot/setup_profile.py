"""
يضبط "واجهة" البوت في تيليجرام عند الإقلاع:
1. زر القائمة الدائم (Menu Button) بجانب حقل الكتابة - يعرض قائمة الأوامر مباشرة.
2. قائمة الأوامر (/menu, /language, /help...) بثلاث لغات (ar/en/fr) حسب لغة عميل تيليجرام.
3. اسم البوت ووصفه القصير/الكامل - هذا بالضبط ما يظهر في معاينة الرابط عند مشاركة
   t.me/YourBotUsername (الوصف القصير) وفي شاشة الترحيب الفارغة قبل أول رسالة (الوصف الكامل).

صورة البوت الشخصية (Profile Photo) لا يوجد لها endpoint في Bot API لتعيينها ذاتيًا -
تُضبط فقط يدويًا عبر BotFather (/setuserpic)، موضّح في docs/deployment.md.
"""

import logging

from aiogram import Bot
from aiogram.types import BotCommand, MenuButtonCommands

from app.locales import SUPPORTED_LANGUAGES, t

logger = logging.getLogger(__name__)

_COMMAND_KEYS = [
    ("start", "cmd_start_desc"),
    ("menu", "cmd_menu_desc"),
    ("language", "cmd_language_desc"),
    ("help", "cmd_help_desc"),
    ("manager", "cmd_manager_desc"),
    ("responsible", "cmd_responsible_desc"),
    ("stop_marketing", "cmd_stop_marketing_desc"),
]


async def setup_bot_profile(bot: Bot) -> None:
    try:
        await bot.set_chat_menu_button(menu_button=MenuButtonCommands())

        for lang in SUPPORTED_LANGUAGES:
            commands = [BotCommand(command=cmd, description=t(lang, desc_key)) for cmd, desc_key in _COMMAND_KEYS]
            await bot.set_my_commands(commands, language_code=lang)

            await bot.set_my_short_description(t(lang, "bot_short_description"), language_code=lang)
            await bot.set_my_description(t(lang, "bot_full_description"), language_code=lang)

        # نسخة افتراضية بدون language_code لعملاء تيليجرام بلغة غير مدعومة (تُعرض كاحتياطي)
        default_commands = [BotCommand(command=cmd, description=t("ar", desc_key)) for cmd, desc_key in _COMMAND_KEYS]
        await bot.set_my_commands(default_commands)

        logger.info("تم ضبط واجهة البوت (الأوامر، زر القائمة، الوصف) بنجاح.")
    except Exception:  # noqa: BLE001
        # لا يجب أن يمنع فشل ضبط الواجهة تشغيل البوت نفسه
        logger.exception("فشل ضبط واجهة البوت (setMyCommands/setChatMenuButton) - البوت سيستمر بالعمل رغم ذلك.")
