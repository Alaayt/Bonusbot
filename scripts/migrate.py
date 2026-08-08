"""
يشغّل alembic upgrade head بأمان عند إقلاع الحاوية.

يتعامل مع حالة خاصة: قواعد بيانات قديمة أُنشئت عبر init_db()/create_all() (قبل إدخال
alembic لهذا المشروع) وليس فيها سجل alembic فعلي - لو شغّلنا "upgrade head" مباشرة
عليها، alembic يحاول إعادة تنفيذ migration الإنشاء الأولى فتفشل بخطأ "table already
exists". نتحقق من العمود الفعلي (last_nav_message_id) بدل الاعتماد فقط على وجود جدول
alembic_version - لأن محاولة سابقة فاشلة قد تكون تركت الجدول موجودًا لكن فارغًا من أي
صف نسخة، وهذا كان يخدع الفحص القديم. نعمل "stamp" على النقطة الصحيحة بدون تنفيذها
فعليًا، قبل تشغيل upgrade head الطبيعي.
"""

import asyncio
import logging

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.common.config import get_settings

logger = logging.getLogger(__name__)

INITIAL_REVISION = "f1b96bce661e"
HEAD_REVISION = "a3d8f0c1e9b2"


async def _inspect_db(database_url: str) -> tuple[set[str], bool]:
    engine = create_async_engine(database_url)
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda sync_conn: set(inspect(sync_conn).get_table_names()))
        has_new_column = False
        if "users" in tables:
            columns = await conn.run_sync(lambda sync_conn: {c["name"] for c in inspect(sync_conn).get_columns("users")})
            has_new_column = "last_nav_message_id" in columns
    await engine.dispose()
    return tables, has_new_column


async def _current_alembic_revision(database_url: str, has_alembic_version_table: bool) -> str | None:
    if not has_alembic_version_table:
        return None
    engine = create_async_engine(database_url)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
        row = result.first()
    await engine.dispose()
    return row[0] if row else None


def main() -> None:
    settings = get_settings()
    tables, has_new_column = asyncio.run(_inspect_db(settings.database_url))
    current_revision = asyncio.run(_current_alembic_revision(settings.database_url, "alembic_version" in tables))

    alembic_cfg = Config("alembic.ini")

    if "users" in tables and current_revision is None:
        target = HEAD_REVISION if has_new_column else INITIAL_REVISION
        logger.warning(
            "قاعدة بيانات قديمة بدون سجل alembic صالح (جدول users موجود، لا يوجد صف نسخة) "
            "- تُعلَّم كأنها عند %s قبل الترقية.",
            target,
        )
        command.stamp(alembic_cfg, target)

    command.upgrade(alembic_cfg, "head")


if __name__ == "__main__":
    main()
