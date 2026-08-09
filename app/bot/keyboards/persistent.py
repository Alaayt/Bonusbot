from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.locales import t


def persistent_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """
    زر ثابت فوق خانة الكتابة (Reply Keyboard) يبقى ظاهرًا دائمًا بغض النظر عن أي كيبورد
    إنلاين (Inline Keyboard) مرفق برسائل أخرى - يفتح القائمة الرئيسية بضغطة واحدة.
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "btn_persistent_menu"))]],
        resize_keyboard=True,
        is_persistent=True,
    )
