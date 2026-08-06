from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.repositories.user_repository import update_user
from app.locales import t

router = Router(name="settings")


@router.message(Command("stop_marketing"))
async def cmd_stop_marketing(message: Message, session: AsyncSession, user: User) -> None:
    lang = user.language or "ar"
    await update_user(session, user, marketing_opt_out=True)
    await message.answer(t(lang, "stop_marketing_confirm"))
