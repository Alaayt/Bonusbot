from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.locales import t


def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(lang, "btn_first_deposit"), callback_data="cat:first_deposit")],
        [InlineKeyboardButton(text=t(lang, "btn_sports"), callback_data="cat:sports")],
        [InlineKeyboardButton(text=t(lang, "btn_casino"), callback_data="cat:casino")],
        [InlineKeyboardButton(text=t(lang, "btn_crypto"), callback_data="cat:crypto")],
        [InlineKeyboardButton(text=t(lang, "btn_tournaments"), callback_data="cat:tournament")],
        [InlineKeyboardButton(text=t(lang, "btn_freebets"), callback_data="cat:freebet")],
        [InlineKeyboardButton(text=t(lang, "btn_cashback"), callback_data="cat:cashback")],
        [InlineKeyboardButton(text=t(lang, "btn_invite"), callback_data="cat:friends")],
        [InlineKeyboardButton(text=t(lang, "btn_find_for_me"), callback_data="action:find_for_me")],
        [InlineKeyboardButton(text=t(lang, "btn_explain_terms"), callback_data="action:explain_terms")],
        [InlineKeyboardButton(text=t(lang, "btn_missing_bonus"), callback_data="action:missing_bonus")],
        [InlineKeyboardButton(text=t(lang, "btn_register"), callback_data="action:register")],
        [InlineKeyboardButton(text=t(lang, "btn_manager"), callback_data="action:manager")],
        [InlineKeyboardButton(text=t(lang, "btn_change_language"), callback_data="action:change_language")],
        [InlineKeyboardButton(text=t(lang, "btn_responsible_gaming"), callback_data="action:responsible_gaming")],
        [InlineKeyboardButton(text=t(lang, "btn_share_bot"), callback_data="action:share_bot")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
