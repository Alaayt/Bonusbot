"""
مرسِل الرسائل "التنقلية" (قوائم، أسئلة بأزرار كـ اختيار اللغة/الدولة/القائمة الرئيسية):
يحذف آخر رسالة تنقّل أرسلها البوت لنفس المستخدم قبل إرسال الجديدة، حتى تبقى المحادثة نظيفة
بدل تراكم قوائم قديمة. لا يُستخدم للرسائل المحتوى-معلوماتية (شرح عرض، رد المدير...) التي يجب
أن تبقى في السجل.
"""

import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.repositories.user_repository import update_user

logger = logging.getLogger(__name__)


async def send_nav(
    target: Message | CallbackQuery,
    user: User,
    session: AsyncSession,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> Message:
    message = target.message if isinstance(target, CallbackQuery) else target
    bot = message.bot

    if user.last_nav_message_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=user.last_nav_message_id)
            logger.info("nav: deleted previous message %s in chat %s", user.last_nav_message_id, message.chat.id)
        except TelegramBadRequest as exc:
            logger.warning(
                "nav: failed to delete previous message %s in chat %s: %s", user.last_nav_message_id, message.chat.id, exc
            )
    else:
        logger.info("nav: no previous nav message tracked for user %s yet", user.telegram_id)

    sent = await message.answer(text, reply_markup=reply_markup)
    await update_user(session, user, last_nav_message_id=sent.message_id)
    return sent
