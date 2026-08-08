"""
يشغّل alembic upgrade head بأمان عند إقلاع الحاوية.

يتعامل مع حالة خاصة: قواعد بيانات قديمة أُنشئت عبر init_db()/create_all() (قبل إدخال
alembic لهذا المشروع) وليس فيها جدول alembic_version - لو شغّلنا "upgrade head" مباشرة
عليها، alembic يحاول إعادة تنفيذ migration الإنشاء الأولى فتفشل بخطأ "table already
exists". نكتشف هذي الحالة (جدول users موجود لكن alembic_version غير موجود) ونعمل
"stamp" على الـ revision الأولية بدون تنفيذها فعليًا، قبل تشغيل upgrade head الطبيعي.
"""

import asyncio
import logging

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app.common.config import get_settings

logger = logging.getLogger(__name__)

INITIAL_REVISION = "f1b96bce661e"


async def _get_existing_tables(database_url: str) -> set[str]:
    engine = create_async_engine(database_url)
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda sync_conn: set(inspect(sync_conn).get_table_names()))
    await engine.dispose()
    return tables


def main() -> None:
    settings = get_settings()
    existing_tables = asyncio.run(_get_existing_tables(settings.database_url))

    alembic_cfg = Config("alembic.ini")

    if "users" in existing_tables and "alembic_version" not in existing_tables:
        logger.warning(
            "قاعدة بيانات قديمة بدون سجل alembic - تُعلَّم كأنها عند %s قبل الترقية.", INITIAL_REVISION
        )
        command.stamp(alembic_cfg, INITIAL_REVISION)

    command.upgrade(alembic_cfg, "head")


if __name__ == "__main__":
    main()
