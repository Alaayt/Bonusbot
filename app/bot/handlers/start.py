from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import age_confirm_keyboard, country_keyboard
from app.bot.keyboards.language import language_keyboard
from app.bot.keyboards.main_menu import main_menu_keyboard
from app.bot.nav import send_nav
from app.bot.states.onboarding import Onboarding
from app.database.models.user import PlayerStage, User
from app.database.repositories.user_repository import update_user
from app.locales import t

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession, user: User) -> None:
    if user.language and user.country_code and user.age_confirmed_adult:
        name = message.from_user.first_name or ""
        await send_nav(
            message, user, session, t(user.language, "welcome_message", name=name), main_menu_keyboard(user.language)
        )
        return
    await state.set_state(Onboarding.choosing_language)
    await send_nav(message, user, session, t("ar", "choose_language"), language_keyboard())


@router.callback_query(F.data.startswith("lang:"))
async def on_language_chosen(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User) -> None:
    lang = callback.data.split(":", 1)[1]
    await update_user(session, user, language=lang)
    await callback.message.edit_text(t(lang, "language_set"))

    if user.country_code and user.age_confirmed_adult:
        await send_nav(callback, user, session, t(lang, "main_menu_title"), main_menu_keyboard(lang))
        await state.clear()
    else:
        await state.set_state(Onboarding.choosing_country)
        await send_nav(callback, user, session, t(lang, "ask_country"), country_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("country:"))
async def on_country_chosen(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User) -> None:
    lang = user.language or "ar"
    code = callback.data.split(":", 1)[1]

    if code == "OTHER":
        await state.set_state(Onboarding.typing_country_name)
        await callback.message.answer(t(lang, "country_other_prompt"))
        await callback.answer()
        return

    await update_user(session, user, country_code=code)

    if user.age_confirmed_adult:
        await send_nav(callback, user, session, t(lang, "main_menu_title"), main_menu_keyboard(lang))
        await state.clear()
    else:
        await state.set_state(Onboarding.confirming_age)
        await send_nav(callback, user, session, t(lang, "ask_age"), age_confirm_keyboard(lang))
    await callback.answer()


@router.message(Onboarding.typing_country_name)
async def on_country_typed(message: Message, state: FSMContext, session: AsyncSession, user: User) -> None:
    lang = user.language or "ar"
    await update_user(session, user, country_code=(message.text or "OTHER")[:5].upper())

    if user.age_confirmed_adult:
        await send_nav(message, user, session, t(lang, "main_menu_title"), main_menu_keyboard(lang))
        await state.clear()
    else:
        await state.set_state(Onboarding.confirming_age)
        await send_nav(message, user, session, t(lang, "ask_age"), age_confirm_keyboard(lang))


@router.callback_query(F.data == "age:no")
async def on_age_no(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User) -> None:
    lang = user.language or "ar"
    await update_user(session, user, age_confirmed_adult=False, is_minor_flagged=True, stage=PlayerStage.INELIGIBLE)
    await callback.message.edit_text(t(lang, "minor_blocked"))
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "age:yes")
async def on_age_yes(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User) -> None:
    lang = user.language or "ar"
    await update_user(session, user, age_confirmed_adult=True, stage=PlayerStage.EXPLORING)
    name = callback.from_user.first_name or ""
    await callback.message.edit_text(t(lang, "age_confirm_yes"))
    await send_nav(callback, user, session, t(lang, "welcome_message", name=name), main_menu_keyboard(lang))
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "action:change_language")
async def on_change_language(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User) -> None:
    await state.set_state(Onboarding.choosing_language)
    await send_nav(callback, user, session, t("ar", "choose_language"), language_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:main")
async def on_back_to_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User) -> None:
    lang = user.language or "ar"
    await state.clear()
    await send_nav(callback, user, session, t(lang, "main_menu_title"), main_menu_keyboard(lang))
    await callback.answer()
