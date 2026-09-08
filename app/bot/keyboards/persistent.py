from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.locales import t


def persistent_menu_keyboard(lang: str, is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    زر ثابت فوق خانة الكتابة (Reply Keyboard) يبقى ظاهرًا دائمًا بغض النظر عن أي كيبورد
    إنلاين (Inline Keyboard) مرفق برسائل أخرى - يفتح القائمة الرئيسية بضغطة واحدة.
    للأدمن فقط، يضاف زر ثابت ثانٍ لفتح لوحة الإدارة مباشرة - Reply Keyboard خاص بمحادثة
    هذا المستخدم تحديدًا، فلا يظهر لأي حد غيره.
    """
    keyboard = [[KeyboardButton(text=t(lang, "btn_persistent_menu"))]]
    if is_admin:
        keyboard.append([KeyboardButton(text=t(lang, "btn_admin_panel"))])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )
