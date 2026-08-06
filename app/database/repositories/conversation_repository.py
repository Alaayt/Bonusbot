from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.conversation import ConversationMessage


async def log_message(
    session: AsyncSession,
    user_id: int,
    telegram_id: int,
    role: str,
    text: str,
    intent: str | None = None,
    promotion_slug: str | None = None,
) -> ConversationMessage:
    message = ConversationMessage(
        user_id=user_id,
        telegram_id=telegram_id,
        role=role,
        text=text,
        intent=intent,
        promotion_slug=promotion_slug,
    )
    session.add(message)
    await session.commit()
    return message


async def get_recent_messages(session: AsyncSession, telegram_id: int, limit: int = 20) -> list[ConversationMessage]:
    result = await session.execute(
        select(ConversationMessage)
        .where(ConversationMessage.telegram_id == telegram_id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(limit)
    )
    return list(reversed(result.scalars().all()))
