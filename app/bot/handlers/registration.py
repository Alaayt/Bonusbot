from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import back_to_menu_keyboard, registration_links_keyboard
from app.common.config import get_settings
from app.database.models.user import PlayerStage, User
from app.database.repositories.alert_repository import create_manager_alert
from app.database.repositories.promotion_meta_repository import log_click
from app.database.repositories.user_repository import update_user
from app.locales import t

router = Router(name="registration")
settings = get_settings()


@router.callback_query(F.data == "action:register")
async def on_register(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    """
    البوت موجّه حصريًا لتسجيل حساب جديد بالبروموكود VIP10IQ - هذا هو المصدر الوحيد
    للاستفادة من العروض عبر البروموكود. لا نسأل بعد الآن "هل لديك حساب؟" في مسار التسجيل
    نفسه، لأن الإجابة لا تغيّر الخطوة المطلوبة: يلزم دائمًا حساب جديد للحصول على عروض
    البروموكود. إن كان لدى المستخدم حساب حالي فعلاً، نوضّح له ذلك صراحة بدل تجاهله.
    """
    lang = user.language or "ar"
    await update_user(session, user, stage=PlayerStage.READY_TO_REGISTER)
    await _send_registration_info(callback, session, user, lang)
    await callback.answer()


async def _send_registration_info(callback: CallbackQuery, session: AsyncSession, user: User, lang: str, has_account: bool | None = None) -> None:
    has_account = user.has_existing_account if has_account is None else has_account

    lines = []
    if has_account:
        lines.append(t(lang, "existing_account_needs_new_one"))
        lines.append("")

    lines += [
        t(lang, "no_account_promo_intro"),
        f"`{settings.promo_code}`",
        t(lang, "promo_where_to_enter"),
    ]

    if not settings.affiliate_registration_url:
        lines.append(f"\n{t(lang, 'registration_link_missing', promo=settings.promo_code)}")

    # الروابط نفسها تُفتح بنقرة واحدة عبر أزرار URL أسفل الرسالة (registration_links_keyboard)
    # بدل نسخ/لصق رابط نصي - تجربة أسرع وأوضح للاعب.
    if settings.affiliate_registration_url or settings.app_download_url:
        keyboard = registration_links_keyboard(lang, settings.affiliate_registration_url, settings.app_download_url)
    else:
        keyboard = back_to_menu_keyboard(lang)

    await callback.message.answer("\n".join(lines), reply_markup=keyboard)

    # خطوة تكملة الملف الشخصي - رسالة منفصلة حتى لا تُغرق رسالة البروموكود بتفاصيل كثيرة دفعة واحدة
    await callback.message.answer(
        f"{t(lang, 'profile_completion_intro')}\n\n"
        f"{t(lang, 'profile_completion_steps')}\n\n"
        f"{t(lang, 'profile_completion_benefit')}\n\n"
        f"{t(lang, 'confirm_bonus_after_signup')}",
        reply_markup=back_to_menu_keyboard(lang),
    )

    await log_click(session, callback.from_user.id, None, "registration_link")
    await create_manager_alert(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        language=lang,
        country_code=user.country_code,
        reason="registration_intent",
        summary=f"طلب المستخدم رابط/بروموكود التسجيل. لديه حساب حالي: {user.has_existing_account}.",
        stage=str(user.stage.value if hasattr(user.stage, 'value') else user.stage),
    )
