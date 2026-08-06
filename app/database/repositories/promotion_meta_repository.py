from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.promotion_meta import AuditLogEntry, PendingUpdate, PromotionClick, PromotionOverride


async def get_override(session: AsyncSession, slug: str) -> PromotionOverride | None:
    result = await session.execute(select(PromotionOverride).where(PromotionOverride.slug == slug))
    return result.scalar_one_or_none()


async def log_click(session: AsyncSession, telegram_id: int, slug: str | None, click_type: str) -> None:
    session.add(PromotionClick(telegram_id=telegram_id, slug=slug, click_type=click_type))
    await session.commit()


async def log_audit(session: AsyncSession, actor_admin_id: int | None, action: str, target_slug: str | None, details: str | None) -> None:
    session.add(AuditLogEntry(actor_admin_id=actor_admin_id, action=action, target_slug=target_slug, details=details))
    await session.commit()


async def create_pending_update(session: AsyncSession, slug: str, new_text: str, source: str, old_text: str | None = None) -> PendingUpdate:
    update = PendingUpdate(slug=slug, new_text=new_text, source=source, old_text=old_text)
    session.add(update)
    await session.commit()
    await session.refresh(update)
    return update


async def list_pending_updates(session: AsyncSession) -> list[PendingUpdate]:
    result = await session.execute(select(PendingUpdate).where(PendingUpdate.status == "pending"))
    return list(result.scalars().all())
