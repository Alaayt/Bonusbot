from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import full_details_keyboard, offers_list_keyboard
from app.bot.nav import send_nav
from app.database.models.user import User
from app.database.repositories.promotion_meta_repository import log_click
from app.locales import t
from app.promotions.services.formatter import format_full_details, format_quick_summary
from app.promotions.services.promotion_store import get_by_category_keywords, get_promotion

# فئات العروض الفعلية بصيغة "<domain>_<type>" (مثل sports_deposit_bonus، casino_weekly_deposit_bonus)
# لذلك كل زر قائمة يطابق أي كلمة مفتاحية *ضمن* نص الفئة (substring)، وليس بادئة صارمة.
CATEGORY_MAP: dict[str, list[str]] = {
    "first_deposit": ["deposit_bonus"],
    "sports": ["sports_"],
    "casino": ["casino_"],
    "crypto": ["crypto_"],
    "tournament": ["tournament"],
    "freebet": ["freebet", "risk_free", "prediction", "raffle"],
    "cashback": ["cashback"],
    "friends": ["affiliate_referral"],
}

router = Router(name="offers")


@router.callback_query(F.data.startswith("cat:"))
async def on_category_selected(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    lang = user.language or "ar"
    cat_key = callback.data.split(":", 1)[1]
    keywords = CATEGORY_MAP.get(cat_key, [cat_key])

    promos = get_by_category_keywords(keywords)
    if not promos:
        # fallback: بحث نصي بالكلمة المفتاحية نفسها عبر كل العروض إن لم تُطابق الفئة مباشرة
        from app.ai.rag.search import get_relevant_promotions

        promos = get_relevant_promotions(cat_key, lang=lang, country_code=user.country_code, limit=8)

    if not promos:
        await callback.message.answer(t(lang, "offer_not_found"))
        await callback.answer()
        return

    items = [(p.slug, p.name(lang)) for p in promos]
    await send_nav(callback, user, session, t(lang, "main_menu_title"), offers_list_keyboard(lang, items))
    await callback.answer()


@router.callback_query(F.data.startswith("offer:"))
async def on_offer_selected(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    lang = user.language or "ar"
    slug = callback.data.split(":", 1)[1]
    promo = get_promotion(slug)

    if promo is None:
        await callback.message.answer(t(lang, "offer_not_found"))
        await callback.answer()
        return

    if promo.status == "expired":
        await callback.message.answer(t(lang, "offer_expired", date=promo.last_checked_at))
        await callback.answer()
        return

    await log_click(session, callback.from_user.id, slug, "promotion_view")
    text = format_quick_summary(promo, lang)
    await callback.message.answer(text, reply_markup=full_details_keyboard(lang, slug), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("offer_full:"))
async def on_offer_full_details(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    lang = user.language or "ar"
    slug = callback.data.split(":", 1)[1]
    promo = get_promotion(slug)

    if promo is None:
        await callback.message.answer(t(lang, "offer_not_found"))
        await callback.answer()
        return

    text = format_full_details(promo, lang)
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()
