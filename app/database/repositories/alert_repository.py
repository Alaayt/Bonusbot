from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.promotion_meta import ManagerAlert


async def create_manager_alert(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    language: str | None,
    country_code: str | None,
    reason: str,
    summary: str,
    stage: str | None,
    promotion_slug: str | None = None,
) -> ManagerAlert:
    alert = ManagerAlert(
        telegram_id=telegram_id,
        username=username,
        language=language,
        country_code=country_code,
        reason=reason,
        promotion_slug=promotion_slug,
        summary=summary,
        stage=stage,
    )
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert
