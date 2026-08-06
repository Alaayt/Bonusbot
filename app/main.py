import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.admin.router import router as admin_router
from app.bot.handlers.chat import router as chat_router
from app.bot.handlers.manager import router as manager_router
from app.bot.handlers.missing_bonus import router as missing_bonus_router
from app.bot.handlers.offers import router as offers_router
from app.bot.handlers.registration import router as registration_router
from app.bot.handlers.settings import router as settings_router
from app.bot.handlers.start import router as start_router
from app.bot.middlewares.db_session import DbSessionMiddleware
from app.bot.middlewares.user_context import UserContextMiddleware
from app.common.config import get_settings
from app.common.logging import setup_logging
from app.database.engine import init_db
from app.promotions.services.promotion_store import get_all_promotions
from app.scheduler.promotion_watcher import start_scheduler

logger = logging.getLogger(__name__)


def _check_promotions_loaded() -> None:
    """
    فحص إقلاع حرج: لو رجع 0 عرض، الأرجح أن مجلد data/promotions فارغ في بيئة التشغيل -
    السبب الشائع جدًا على منصات مثل Railway/Render هو تركيب Volume فارغ فوق مسار /app/data
    نفسه، فيغطي محتوى الصورة (data/promotions, data/raw_sources) المُدمج فيها من COPY . .
    راجع docs/deployment.md قسم "تحذير: Volumes ومسار data/" لحل الموضوع.
    """
    count = len(get_all_promotions())
    if count == 0:
        logger.critical(
            "⚠️ عدد العروض المحمّلة من data/promotions هو 0! على الأغلب مجلد data/ "
            "فارغ في بيئة التشغيل الحالية (سبب شائع: Volume مُركَّب على /app/data يغطي "
            "ملفات العروض المدمجة في صورة Docker). راجع docs/deployment.md قبل المتابعة."
        )
    else:
        logger.info("تم تحميل %d عرضًا من قاعدة المعرفة (data/promotions).", count)


async def main() -> None:
    setup_logging()
    settings = get_settings()

    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN غير مضبوط في .env")

    _check_promotions_loaded()
    await init_db()

    bot = Bot(token=settings.telegram_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(UserContextMiddleware())

    # ترتيب التسجيل مهم: admin أولاً (فلتر صارم)، ثم المسارات المحددة، ثم chat كـ catch-all أخيرًا
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(offers_router)
    dp.include_router(registration_router)
    dp.include_router(manager_router)
    dp.include_router(missing_bonus_router)
    dp.include_router(settings_router)
    dp.include_router(chat_router)

    scheduler = start_scheduler()

    logger.info("البوت بدأ العمل (polling)...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
