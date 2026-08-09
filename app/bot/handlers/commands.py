"""
أوامر Slash إضافية (/menu, /language, /help, /manager, /responsible) تعطي طرقًا
سريعة للوصول لنفس وظائف أزرار القائمة الرئيسية، وتظهر في زر القائمة الدائم (Menu Button)
بجانب حقل الكتابة في تيليجرام بعد تسجيلها عبر setMyCommands في app/main.py.
"""

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import back_to_menu_keyboard
from app.bot.keyboards.language import language_keyboard
from app.bot.keyboards.main_menu import main_menu_keyboard
from app.bot.nav import send_nav
from app.bot.states.onboarding import Onboarding
from app.database.models.user import PlayerStage, User
from app.database.repositories.alert_repository import create_manager_alert
from app.database.repositories.user_repository import update_user
from app.locales import SUPPORTED_LANGUAGES, t

router = Router(name="commands")

_PERSISTENT_MENU_BUTTON_TEXTS = {t(lang, "btn_persistent_menu") for lang in SUPPORTED_LANGUAGES}


@router.message(Command("menu"))
@router.message(F.text.in_(_PERSISTENT_MENU_BUTTON_TEXTS))
async def cmd_menu(message: Message, session: AsyncSession, user: User) -> None:
    lang = user.language or "ar"
    await send_nav(message, user, session, t(lang, "main_menu_title"), main_menu_keyboard(lang))


@router.message(Command("help"))
async def cmd_help(message: Message, user: User) -> None:
    lang = user.language or "ar"
    await message.answer(t(lang, "help_text"), reply_markup=main_menu_keyboard(lang))


@router.message(Command("language"))
async def cmd_language(message: Message, state: FSMContext, session: AsyncSession, user: User) -> None:
    await state.set_state(Onboarding.choosing_language)
    await send_nav(message, user, session, t("ar", "choose_language"), language_keyboard())


@router.message(Command("manager"))
async def cmd_manager(message: Message, session: AsyncSession, user: User) -> None:
    lang = user.language or "ar"
    await update_user(session, user, stage=PlayerStage.NEEDS_HUMAN_MANAGER)

    await create_manager_alert(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        language=lang,
        country_code=user.country_code,
        reason="human_support_requested",
        summary="طلب المستخدم التواصل المباشر مع المدير البشري عبر أمر /manager.",
        stage=str(user.stage.value if hasattr(user.stage, "value") else user.stage),
    )

    await message.answer(t(lang, "manager_contact_intro"), reply_markup=back_to_menu_keyboard(lang))


@router.message(Command("responsible"))
async def cmd_responsible_gaming(message: Message, user: User) -> None:
    lang = user.language or "ar"
    await message.answer(t(lang, "responsible_gaming_text"), reply_markup=back_to_menu_keyboard(lang))


@router.callback_query(F.data == "action:share_bot")
async def on_share_bot(callback: CallbackQuery, user: User) -> None:
    """
    يبعت للمستخدم رسالة جاهزة (صورة البوت + نص ترويجي + رابط) يقدر يفوروردها لأصدقائه -
    هذي رسالة حقيقية مرسلة من البوت فتظهر مضمونة على أي جهاز، بعكس معاينة رابط t.me
    داخل المحادثة اللي تعتمد على كاش تيليجرام غير المضمون.
    """
    lang = user.language or "ar"
    bot = callback.bot
    me = await bot.get_me()
    bot_link = f"https://t.me/{me.username}"
    caption = t(lang, "share_bot_caption", bot_link=bot_link)

    photo_file_id = None
    try:
        chat_info = await bot.get_chat(me.id)
        if chat_info.photo:
            photo_file_id = chat_info.photo.big_file_id
    except TelegramAPIError:
        photo_file_id = None

    if photo_file_id:
        await callback.message.answer_photo(photo=photo_file_id, caption=caption)
    else:
        await callback.message.answer(caption)
    await callback.answer()
