from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.common.config import get_settings


def is_admin_id(telegram_id: int) -> bool:
    return telegram_id in get_settings().admin_id_list


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user is not None and is_admin_id(message.from_user.id)
