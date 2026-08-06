from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import back_to_menu_keyboard
from app.common.config import get_settings
from app.database.models.user import PlayerStage, User
from app.database.repositories.alert_repository import create_manager_alert
from app.database.repositories.user_repository import update_user
from app.locales import t

router = Router(name="manager")
settings = get_settings()


@router.callback_query(F.data == "action:manager")
async def on_contact_manager(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    lang = user.language or "ar"
    await update_user(session, user, stage=PlayerStage.NEEDS_HUMAN_MANAGER)

    await create_manager_alert(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        language=lang,
        country_code=user.country_code,
        reason="human_support_requested",
        summary="طلب المستخدم التواصل المباشر مع المدير البشري من القائمة الرئيسية.",
        stage=str(user.stage.value if hasattr(user.stage, "value") else user.stage),
    )

    await callback.message.answer(t(lang, "manager_contact_intro"), reply_markup=back_to_menu_keyboard(lang))
    await callback.answer(t(lang, "manager_notified"))


@router.callback_query(F.data == "action:responsible_gaming")
async def on_responsible_gaming(callback: CallbackQuery, user: User) -> None:
    lang = user.language or "ar"
    await callback.message.answer(t(lang, "responsible_gaming_text"), reply_markup=back_to_menu_keyboard(lang))
    await callback.answer()
