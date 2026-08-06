from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇸🇦 العربية", callback_data="lang:ar")],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
            [InlineKeyboardButton(text="🇫🇷 Français", callback_data="lang:fr")],
        ]
    )
