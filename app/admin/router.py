"""
لوحة إدارة مبسّطة تعمل بالكامل عبر أوامر تيليجرام (بدون واجهة ويب منفصلة)، متاحة فقط
لمعرّفات ADMIN_IDS في متغيرات البيئة. هذا يحقق متطلبات "رفع PDF أو لصق نص الشروط يدويًا"
و"مراجعة التحديثات" و"الإحصائيات" و"الإعلانات" دون الحاجة لبناء تطبيق ويب منفصل.
"""

import csv
import io
from datetime import datetime, timezone

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.filters.admin_filter import IsAdmin
from app.common.config import get_settings
from app.database.models.conversation import ConversationMessage
from app.database.models.promotion_meta import AdminCountry, PendingUpdate, PromotionClick, PromotionOverride
from app.database.models.user import User
from app.database.repositories.promotion_meta_repository import (
    create_pending_update,
    get_override,
    list_pending_updates,
    log_audit,
)
from app.promotions.services.promotion_store import get_all_promotions, reload_promotions

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

settings = get_settings()


class AdminUpload(StatesGroup):
    waiting_slug = State()
    waiting_text = State()


class AdminPanel(StatesGroup):
    waiting_broadcast_text = State()


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 إحصائيات", callback_data="admin:stats")],
            [InlineKeyboardButton(text="🏆 أكثر العروض طلبًا", callback_data="admin:top_offers")],
            [InlineKeyboardButton(text="📝 التحديثات المعلّقة", callback_data="admin:pending")],
            [InlineKeyboardButton(text="📢 إرسال إعلان لكل المستخدمين", callback_data="admin:broadcast_start")],
            [InlineKeyboardButton(text="📋 تصدير قائمة المستخدمين (CSV)", callback_data="admin:export_users")],
            [InlineKeyboardButton(text="⬅️ رجوع للقائمة الرئيسية", callback_data="menu:main")],
        ]
    )


ADMIN_HELP = (
    "*لوحة الإدارة*\n\n"
    "/admin_stats - إحصائيات عامة\n"
    "/admin_top_offers - أكثر العروض طلبًا\n"
    "/admin_pending - مراجعة التحديثات المعلقة\n"
    "/admin_update_offer <slug> - رفع نص شروط جديد لعرض (يدويًا)\n"
    "/admin_toggle <slug> - تفعيل/تعطيل عرض\n"
    "/admin_add_country <code> <ar>|<en>|<fr> - إضافة دولة جديدة\n"
    "/admin_broadcast <نص> - إرسال إعلان لكل المستخدمين (يستبعد من طلب إيقاف التسويق)\n"
    "/admin_users - تصدير قائمة كل المشتركين كملف CSV\n"
)


@router.message(Command("admin"))
async def admin_help(message: Message) -> None:
    await message.answer(ADMIN_HELP, reply_markup=admin_panel_keyboard(), parse_mode="Markdown")


async def _stats_text(session: AsyncSession) -> str:
    conv_count = (await session.execute(select(func.count(ConversationMessage.id)))).scalar_one()
    reg_clicks = (
        await session.execute(select(func.count(PromotionClick.id)).where(PromotionClick.click_type == "registration_link"))
    ).scalar_one()
    total_promos = len(get_all_promotions())
    verified = len([p for p in get_all_promotions() if p.verification_status == "verified"])

    return (
        "*إحصائيات عامة*\n\n"
        f"عدد رسائل المحادثات: {conv_count}\n"
        f"نقرات رابط التسجيل: {reg_clicks}\n"
        f"عدد العروض في قاعدة المعرفة: {total_promos}\n"
        f"عروض موثقة بالكامل: {verified}"
    )


@router.message(Command("admin_stats"))
async def admin_stats(message: Message, session: AsyncSession) -> None:
    await message.answer(await _stats_text(session), parse_mode="Markdown")


async def _top_offers_text(session: AsyncSession) -> str | None:
    result = await session.execute(
        select(PromotionClick.slug, func.count(PromotionClick.id).label("cnt"))
        .where(PromotionClick.slug.is_not(None))
        .group_by(PromotionClick.slug)
        .order_by(func.count(PromotionClick.id).desc())
        .limit(10)
    )
    rows = result.all()
    if not rows:
        return None
    return "*أكثر العروض طلبًا:*\n\n" + "\n".join(f"{slug}: {cnt}" for slug, cnt in rows)


@router.message(Command("admin_top_offers"))
async def admin_top_offers(message: Message, session: AsyncSession) -> None:
    text = await _top_offers_text(session)
    if text is None:
        await message.answer("لا توجد بيانات نقرات بعد.")
        return
    await message.answer(text, parse_mode="Markdown")


async def _send_pending(bot: Bot, chat_id: int, session: AsyncSession) -> bool:
    pending = await list_pending_updates(session)
    if not pending:
        return False
    for update in pending[:10]:
        preview = update.new_text[:300] + ("…" if len(update.new_text) > 300 else "")
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ موافقة", callback_data=f"padm_approve:{update.id}"),
                    InlineKeyboardButton(text="❌ رفض", callback_data=f"padm_reject:{update.id}"),
                ]
            ]
        )
        await bot.send_message(
            chat_id,
            f"*تحديث #{update.id} - {update.slug}*\nالمصدر: {update.source}\n\n{preview}",
            reply_markup=kb,
            parse_mode="Markdown",
        )
    return True


@router.message(Command("admin_pending"))
async def admin_pending(message: Message, session: AsyncSession) -> None:
    has_pending = await _send_pending(message.bot, message.chat.id, session)
    if not has_pending:
        await message.answer("لا توجد تحديثات معلّقة حاليًا.")


@router.callback_query(F.data.startswith("padm_approve:"))
async def approve_pending(callback: CallbackQuery, session: AsyncSession) -> None:
    update_id = int(callback.data.split(":", 1)[1])
    update = await session.get(PendingUpdate, update_id)
    if update is None:
        await callback.answer("غير موجود")
        return
    update.status = "approved"
    update.reviewed_by_admin_id = callback.from_user.id
    update.reviewed_at = datetime.now(timezone.utc)
    await session.commit()
    await log_audit(session, callback.from_user.id, "approve_pending_update", update.slug, f"update_id={update_id}")
    await callback.message.edit_text(callback.message.text + "\n\n✅ تمت الموافقة - يرجى تحديث ملف JSON يدويًا في data/promotions/ بناءً على هذا النص المعتمد ثم استدعاء reload.")
    await callback.answer()


@router.callback_query(F.data.startswith("padm_reject:"))
async def reject_pending(callback: CallbackQuery, session: AsyncSession) -> None:
    update_id = int(callback.data.split(":", 1)[1])
    update = await session.get(PendingUpdate, update_id)
    if update is None:
        await callback.answer("غير موجود")
        return
    update.status = "rejected"
    update.reviewed_by_admin_id = callback.from_user.id
    update.reviewed_at = datetime.now(timezone.utc)
    await session.commit()
    await log_audit(session, callback.from_user.id, "reject_pending_update", update.slug, f"update_id={update_id}")
    await callback.message.edit_text(callback.message.text + "\n\n❌ تم الرفض.")
    await callback.answer()


@router.message(Command("admin_update_offer"))
async def admin_update_offer_start(message: Message, state: FSMContext) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("الاستخدام: /admin_update_offer <slug>\nثم أرسل نص الشروط الكامل أو ملف PDF في الرسالة التالية.")
        return
    slug = parts[1].strip()
    await state.set_state(AdminUpload.waiting_text)
    await state.update_data(slug=slug)
    await message.answer(f"تمام، أرسل الآن نص الشروط الكامل للعرض `{slug}` (أو ارفع ملف PDF).", parse_mode="Markdown")


@router.message(AdminUpload.waiting_text, F.document)
async def admin_update_offer_pdf(message: Message, state: FSMContext, session: AsyncSession) -> None:
    from app.promotions.parsers.pdf_extractor import extract_text_from_pdf_bytes

    data = await state.get_data()
    slug = data.get("slug")

    file = await message.bot.get_file(message.document.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    text = extract_text_from_pdf_bytes(file_bytes.read())

    await create_pending_update(session, slug=slug, new_text=text, source="admin_upload")
    await message.answer(f"تم استلام ملف PDF لعرض `{slug}` وحفظه كتحديث معلّق بانتظار المراجعة (/admin_pending).", parse_mode="Markdown")
    await state.clear()


@router.message(AdminUpload.waiting_text)
async def admin_update_offer_text(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    slug = data.get("slug")
    await create_pending_update(session, slug=slug, new_text=message.text or "", source="admin_upload")
    await message.answer(f"تم حفظ النص لعرض `{slug}` كتحديث معلّق بانتظار المراجعة (/admin_pending).", parse_mode="Markdown")
    await state.clear()


@router.message(Command("admin_toggle"))
async def admin_toggle_offer(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("الاستخدام: /admin_toggle <slug>")
        return
    slug = parts[1].strip()

    override = await get_override(session, slug)
    if override is None:
        override = PromotionOverride(slug=slug, is_disabled=True)
        session.add(override)
    else:
        override.is_disabled = not override.is_disabled
    override.updated_by_admin_id = message.from_user.id
    await session.commit()

    await log_audit(session, message.from_user.id, "toggle_offer", slug, f"is_disabled={override.is_disabled}")
    reload_promotions()
    await message.answer(f"العرض `{slug}` الآن: {'معطّل ❌' if override.is_disabled else 'مفعّل ✅'}", parse_mode="Markdown")


@router.message(Command("admin_add_country"))
async def admin_add_country(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or "|" not in parts[2]:
        await message.answer("الاستخدام: /admin_add_country <code> <اسم عربي>|<English name>|<nom français>")
        return
    code = parts[1].strip().upper()
    names = parts[2].split("|")
    if len(names) != 3:
        await message.answer("يجب إدخال 3 أسماء مفصولة بـ | (عربي|إنجليزي|فرنسي)")
        return

    country = AdminCountry(code=code, name_ar=names[0].strip(), name_en=names[1].strip(), name_fr=names[2].strip(), added_by_admin_id=message.from_user.id)
    session.add(country)
    await session.commit()
    await log_audit(session, message.from_user.id, "add_country", None, f"code={code}")
    await message.answer(f"تمت إضافة الدولة {code} بنجاح ✅")


async def _run_broadcast(bot: Bot, admin_id: int, session: AsyncSession, text: str) -> tuple[int, int]:
    result = await session.execute(select(User).where(User.marketing_opt_out.is_(False)))
    users = result.scalars().all()

    sent = 0
    for u in users:
        try:
            await bot.send_message(u.telegram_id, text)
            sent += 1
        except Exception:  # noqa: BLE001
            continue

    await log_audit(session, admin_id, "broadcast", None, f"sent={sent}/{len(users)}")
    return sent, len(users)


@router.message(Command("admin_broadcast"))
async def admin_broadcast(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("الاستخدام: /admin_broadcast <نص الإعلان>")
        return
    sent, total = await _run_broadcast(message.bot, message.from_user.id, session, parts[1])
    await message.answer(f"تم إرسال الإعلان إلى {sent} من أصل {total} مستخدمًا (استُبعد من طلب إيقاف الرسائل الترويجية).")


async def _build_users_csv(session: AsyncSession) -> tuple[BufferedInputFile, int] | None:
    result = await session.execute(select(User).order_by(User.created_at))
    users = result.scalars().all()
    if not users:
        return None

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "telegram_id", "username", "first_name", "language", "country_code",
        "has_existing_account", "stage", "marketing_opt_out", "created_at",
    ])
    for u in users:
        writer.writerow([
            u.telegram_id,
            u.username or "",
            u.first_name or "",
            u.language or "",
            u.country_code or "",
            u.has_existing_account if u.has_existing_account is not None else "",
            u.stage.value if hasattr(u.stage, "value") else u.stage,
            u.marketing_opt_out,
            u.created_at.isoformat() if u.created_at else "",
        ])

    file_bytes = buffer.getvalue().encode("utf-8-sig")  # BOM حتى يفتح إكسل الملف بترميز صحيح
    filename = f"bonusbot_users_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.csv"
    return BufferedInputFile(file_bytes, filename=filename), len(users)


@router.message(Command("admin_users"))
async def admin_users_export(message: Message, session: AsyncSession) -> None:
    export = await _build_users_csv(session)
    if export is None:
        await message.answer("ما فيه أي مستخدم مسجّل بعد.")
        return
    file, count = export
    await message.answer_document(file, caption=f"📋 {count} مستخدم مسجّل بالبوت.")


@router.callback_query(F.data == "admin:panel")
async def on_admin_panel(callback: CallbackQuery) -> None:
    await callback.message.answer("*🛠 لوحة الإدارة*\n\nاختر إجراء 👇", reply_markup=admin_panel_keyboard(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def on_admin_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.message.answer(await _stats_text(session), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "admin:top_offers")
async def on_admin_top_offers(callback: CallbackQuery, session: AsyncSession) -> None:
    text = await _top_offers_text(session)
    await callback.message.answer(text or "لا توجد بيانات نقرات بعد.", parse_mode="Markdown" if text else None)
    await callback.answer()


@router.callback_query(F.data == "admin:pending")
async def on_admin_pending(callback: CallbackQuery, session: AsyncSession) -> None:
    has_pending = await _send_pending(callback.bot, callback.message.chat.id, session)
    if not has_pending:
        await callback.message.answer("لا توجد تحديثات معلّقة حاليًا.")
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast_start")
async def on_admin_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminPanel.waiting_broadcast_text)
    await callback.message.answer("أرسل الآن نص الإعلان اللي تبي توزّعه على كل المستخدمين:")
    await callback.answer()


@router.message(AdminPanel.waiting_broadcast_text)
async def on_admin_broadcast_text(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    sent, total = await _run_broadcast(message.bot, message.from_user.id, session, message.text or "")
    await message.answer(f"تم إرسال الإعلان إلى {sent} من أصل {total} مستخدمًا (استُبعد من طلب إيقاف الرسائل الترويجية).")


@router.callback_query(F.data == "admin:export_users")
async def on_admin_export_users(callback: CallbackQuery, session: AsyncSession) -> None:
    export = await _build_users_csv(session)
    if export is None:
        await callback.message.answer("ما فيه أي مستخدم مسجّل بعد.")
        await callback.answer()
        return
    file, count = export
    await callback.message.answer_document(file, caption=f"📋 {count} مستخدم مسجّل بالبوت.")
    await callback.answer()
