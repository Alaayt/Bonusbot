from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from app.database.repositories.user_repository import get_or_create_user


class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session = data["session"]
        tg_user = None
        if isinstance(event, Update):
            if event.message:
                tg_user = event.message.from_user
            elif event.callback_query:
                tg_user = event.callback_query.from_user

        if tg_user is not None:
            user = await get_or_create_user(session, tg_user.id, tg_user.username, tg_user.first_name)
            data["user"] = user
            data["lang"] = user.language or "ar"

        return await handler(event, data)
