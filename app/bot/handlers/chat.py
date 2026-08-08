from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import generate_reply
from app.ai.safety.guardrails import (
    detect_loss_chasing,
    detect_minor_claim,
    detect_prompt_injection_attempt,
    detect_profit_guarantee_request,
    scrub_sensitive_data,
)
from app.bot.keyboards.common import back_to_menu_keyboard, has_account_keyboard, registration_links_keyboard
from app.bot.nav import send_nav
from app.common.config import get_settings
from app.database.models.user import PlayerStage, User
from app.database.repositories.conversation_repository import get_recent_messages, log_message
from app.database.repositories.user_repository import update_user
from app.locales import t

router = Router(name="chat")
settings = get_settings()

MAX_HISTORY = 12

_REGISTRATION_OR_APP_KEYWORDS = [
    "سجل", "تسجيل", "حساب جديد", "افتح حساب", "رابط التسجيل", "رابط تسجيل",
    "تحميل", "التطبيق", "تنزيل",
    "register", "sign up", "signup", "create account", "download", " app ", "app.",
    "s'inscrire", "inscription", "télécharger", "application",
]


def _wants_registration_or_app(text: str) -> bool:
    lowered = f" {text.lower()} "
    return any(keyword in lowered for keyword in _REGISTRATION_OR_APP_KEYWORDS)


@router.callback_query(F.data == "action:find_for_me")
async def on_find_for_me(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    """
    نسأل عن حالة الحساب هنا (وليس في مسار التسجيل نفسه) لأنها مفيدة لتخصيص التوصية:
    مثلاً صاحب حساب حالي يُنصح بعروض تناسب حسابه بجانب تشجيعه على حساب جديد بالبروموكود،
    بينما التسجيل الفعلي بالبروموكود يبقى دائمًا عبر حساب جديد بغض النظر عن الإجابة هنا.
    """
    lang = user.language or "ar"
    if user.has_existing_account is None:
        await send_nav(callback, user, session, t(lang, "ask_has_account"), has_account_keyboard(lang))
        await callback.answer()
        return
    await send_nav(callback, user, session, t(lang, "ask_sport_or_casino"), back_to_menu_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("account:"))
async def on_account_status_for_recommendation(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    lang = user.language or "ar"
    has_account = callback.data.split(":", 1)[1] == "has"
    await update_user(session, user, has_existing_account=has_account)
    await send_nav(callback, user, session, t(lang, "ask_sport_or_casino"), back_to_menu_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "action:explain_terms")
async def on_explain_terms(callback: CallbackQuery, user: User) -> None:
    lang = user.language or "ar"
    await callback.message.answer(t(lang, "offer_not_found") if False else "اكتب اسم العرض اللي تحب أشرح شروطه 👇", reply_markup=back_to_menu_keyboard(lang))
    await callback.answer()


@router.message(F.text & ~F.text.startswith("/"))
async def on_free_text(message: Message, state: FSMContext, session: AsyncSession, user: User) -> None:
    """يلتقط أي رسالة نصية حرة (خارج FSM الأخرى) ويحوّلها لـ Claude مع سياق قاعدة المعرفة."""
    current_state = await state.get_state()
    if current_state is not None:
        return  # حالات FSM الأخرى (missing_bonus، onboarding) لها معالجاتها الخاصة

    lang = user.language or "ar"
    text = message.text or ""

    if detect_minor_claim(text):
        await update_user(session, user, is_minor_flagged=True, age_confirmed_adult=False, stage=PlayerStage.INELIGIBLE)
        await message.answer(t(lang, "minor_blocked"))
        return

    if detect_prompt_injection_attempt(text):
        await message.answer(t(lang, "unclear_message"), reply_markup=back_to_menu_keyboard(lang))
        return

    extra_sections = []
    if detect_loss_chasing(text):
        await message.answer(t(lang, "loss_chasing_warning"), reply_markup=back_to_menu_keyboard(lang))
        return

    if detect_profit_guarantee_request(text):
        extra_sections.append("تنبيه: المستخدم طلب صراحة ضمان ربح. ذكّره بوضوح أنه لا يمكن ضمان الربح ولا تعده بذلك، ثم اشرح العرض بدقة إن سأل عن واحد.")

    safe_text = scrub_sensitive_data(text)

    await log_message(session, user.id, message.from_user.id, "user", safe_text)
    history_rows = await get_recent_messages(session, message.from_user.id, limit=MAX_HISTORY)
    history = [{"role": ("user" if m.role == "user" else "assistant"), "content": m.text} for m in history_rows[:-1]]

    reply = await generate_reply(
        user_message=safe_text,
        lang=lang,
        country_code=user.country_code,
        has_account=user.has_existing_account,
        stage=str(user.stage.value if hasattr(user.stage, "value") else user.stage),
        conversation_history=history,
        extra_system_sections=extra_sections or None,
    )

    await log_message(session, user.id, message.from_user.id, "assistant", reply)

    # لو كان اللاعب يسأل عن التسجيل أو تحميل التطبيق، أرفق أزرار نقرة-واحدة فعلية
    # بدل ما يعتمد فقط على الرابط النصي اللي كتبه النموذج داخل الرد.
    if _wants_registration_or_app(safe_text) and (settings.affiliate_registration_url or settings.app_download_url):
        keyboard = registration_links_keyboard(lang, settings.affiliate_registration_url, settings.app_download_url)
    else:
        keyboard = back_to_menu_keyboard(lang)

    await message.answer(reply, reply_markup=keyboard)
