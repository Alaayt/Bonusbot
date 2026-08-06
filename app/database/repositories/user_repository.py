from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import PlayerStage, User


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str | None, first_name: str | None) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, username=username, first_name=first_name, stage=PlayerStage.NEW)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def update_user(session: AsyncSession, user: User, **fields) -> User:
    for key, value in fields.items():
        setattr(user, key, value)
    await session.commit()
    await session.refresh(user)
    return user
