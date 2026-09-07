from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.common.countries import DEFAULT_SUPPORTED_COUNTRIES
from app.locales import t


def country_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for code, names in DEFAULT_SUPPORTED_COUNTRIES.items():
        row.append(InlineKeyboardButton(text=names.get(lang, names["en"]), callback_data=f"country:{code}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def age_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "age_confirm_yes"), callback_data="age:yes")],
            [InlineKeyboardButton(text=t(lang, "age_confirm_no"), callback_data="age:no")],
        ]
    )


def has_account_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_has_account"), callback_data="account:has")],
            [InlineKeyboardButton(text=t(lang, "btn_no_account"), callback_data="account:none")],
        ]
    )


def back_to_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t(lang, "btn_back_to_menu"), callback_data="menu:main")]]
    )


def offer_summary_keyboard(lang: str, slug: str, offer_url: str | None = None) -> InlineKeyboardMarkup:
    rows = []
    if offer_url:
        rows.append([InlineKeyboardButton(text=t(lang, "btn_open_offer"), url=offer_url)])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_full_details"), callback_data=f"offer_full:{slug}")])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back_to_menu"), callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def offer_full_details_keyboard(lang: str, offer_url: str | None = None) -> InlineKeyboardMarkup:
    rows = []
    if offer_url:
        rows.append([InlineKeyboardButton(text=t(lang, "btn_open_offer"), url=offer_url)])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back_to_menu"), callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def offers_list_keyboard(lang: str, slugs_and_names: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=name, callback_data=f"offer:{slug}")] for slug, name in slugs_and_names]
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back_to_menu"), callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def registration_links_keyboard(lang: str, registration_url: str, app_download_url: str) -> InlineKeyboardMarkup:
    """أزرار قابلة للنقر مباشرة (URL buttons) تفتح رابط التسجيل/التطبيق بنقرة واحدة،
    بدل نسخ ولصق رابط نصي. تُستبعد أي رابط غير مُعد بعد في .env بدل عرض زر مكسور."""
    rows = []
    if registration_url:
        rows.append([InlineKeyboardButton(text=t(lang, "btn_open_registration"), url=registration_url)])
    if app_download_url:
        rows.append([InlineKeyboardButton(text=t(lang, "btn_open_app_download"), url=app_download_url)])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back_to_menu"), callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def manager_gift_keyboard(lang: str, manager_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_contact_manager_gift"), url=manager_url)],
            [InlineKeyboardButton(text=t(lang, "btn_back_to_menu"), callback_data="menu:main")],
        ]
    )
