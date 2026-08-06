from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.safety.guardrails import scrub_sensitive_data
from app.bot.keyboards.common import back_to_menu_keyboard
from app.bot.states.onboarding import MissingBonusFlow
from app.database.models.user import User
from app.database.repositories.alert_repository import create_manager_alert
from app.locales import t

router = Router(name="missing_bonus")


@router.callback_query(F.data == "action:missing_bonus")
async def start_missing_bonus_flow(callback: CallbackQuery, state: FSMContext, user: User) -> None:
    lang = user.language or "ar"
    await state.set_state(MissingBonusFlow.asking_offer_name)
    await state.update_data(answers={})
    await callback.message.answer(t(lang, "missing_bonus_start"))
    await callback.answer()


@router.message(MissingBonusFlow.asking_offer_name)
async def ask_country_currency(message: Message, state: FSMContext, user: User) -> None:
    lang = user.language or "ar"
    data = await state.get_data()
    answers = data.get("answers", {})
    answers["offer_name"] = message.text
    await state.update_data(answers=answers)
    await state.set_state(MissingBonusFlow.asking_country_currency)
    await message.answer(t(lang, "missing_bonus_ask_country_currency"))


@router.message(MissingBonusFlow.asking_country_currency)
async def ask_participate_button(message: Message, state: FSMContext, user: User) -> None:
    lang = user.language or "ar"
    data = await state.get_data()
    answers = data.get("answers", {})
    answers["country_currency"] = message.text
    await state.update_data(answers=answers)
    await state.set_state(MissingBonusFlow.asking_participate_button)
    await message.answer(t(lang, "missing_bonus_ask_participate_button"))


@router.message(MissingBonusFlow.asking_participate_button)
async def ask_selected_before_deposit(message: Message, state: FSMContext, user: User) -> None:
    lang = user.language or "ar"
    data = await state.get_data()
    answers = data.get("answers", {})
    answers["participate_button"] = message.text
    await state.update_data(answers=answers)
    await state.set_state(MissingBonusFlow.asking_selected_before_deposit)
    await message.answer(t(lang, "missing_bonus_ask_selected_before_deposit"))


@router.message(MissingBonusFlow.asking_selected_before_deposit)
async def ask_promo_entered(message: Message, state: FSMContext, user: User) -> None:
    lang = user.language or "ar"
    data = await state.get_data()
    answers = data.get("answers", {})
    answers["selected_before_deposit"] = message.text
    await state.update_data(answers=answers)
    await state.set_state(MissingBonusFlow.asking_promo_entered)
    await message.answer(t(lang, "missing_bonus_ask_promo_entered"))


@router.message(MissingBonusFlow.asking_promo_entered)
async def ask_deposit_time_amount(message: Message, state: FSMContext, user: User) -> None:
    lang = user.language or "ar"
    data = await state.get_data()
    answers = data.get("answers", {})
    answers["promo_entered"] = message.text
    await state.update_data(answers=answers)
    await state.set_state(MissingBonusFlow.asking_deposit_time_amount)
    await message.answer(t(lang, "missing_bonus_ask_deposit_time_amount"))


@router.message(MissingBonusFlow.asking_deposit_time_amount)
async def finish_missing_bonus_flow(message: Message, state: FSMContext, session: AsyncSession, user: User) -> None:
    lang = user.language or "ar"
    data = await state.get_data()
    answers = data.get("answers", {})
    answers["deposit_time_amount"] = scrub_sensitive_data(message.text or "")

    hypothesis = _guess_hypothesis(answers)
    await message.answer(t(lang, "missing_bonus_no_certain_fix", hypothesis=hypothesis), reply_markup=back_to_menu_keyboard(lang))

    summary_lines = [f"{k}: {v}" for k, v in answers.items()]
    await create_manager_alert(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        language=lang,
        country_code=user.country_code,
        reason="missing_bonus",
        summary="مشكلة عدم وصول بونص:\n" + "\n".join(summary_lines),
        stage=str(user.stage.value if hasattr(user.stage, "value") else user.stage),
        promotion_slug=None,
    )

    await state.clear()


def _guess_hypothesis(answers: dict) -> str:
    participate = (answers.get("participate_button") or "").lower()
    selected = (answers.get("selected_before_deposit") or "").lower()
    promo = (answers.get("promo_entered") or "").lower()

    negative_markers = ["لا", "no", "non", "ما", "لم"]

    if any(m in participate for m in negative_markers):
        return "يبدو أنك لم تضغط زر \"المشاركة\" في صفحة العرض قبل الإيداع، وهذا مطلوب لبعض العروض"
    if any(m in selected for m in negative_markers):
        return "يبدو أنك لم تفعّل الاشتراك في عروض المكافآت بإعدادات حسابك قبل الإيداع"
    if any(m in promo for m in negative_markers):
        return "يبدو أنك لم تُدخل البروموكود VIP10IQ أثناء التسجيل، وبعض العروض تتطلب ذلك تحديدًا لحساب جديد"
    return "قد يكون السبب مرتبطًا بوسيلة الدفع أو توقيت الإيداع أو مدة إضافة المكافأة المتوقعة"
