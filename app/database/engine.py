from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.config import get_settings
from app.database.base import Base

settings = get_settings()


def _ensure_sqlite_directory_exists(database_url: str) -> None:
    """
    ينشئ مجلد ملف SQLite تلقائيًا إن لم يكن موجودًا (مثلاً data/db/ على منصة تركّب Volume
    على مسار فرعي جديد لا يُنشئه Docker تلقائيًا قبل أول اتصال). لا يفعل شيئًا لقواعد
    بيانات غير SQLite (PostgreSQL في الإنتاج مثلاً).
    """
    if "sqlite" not in database_url:
        return
    db_path = database_url.split("///")[-1]
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_directory_exists(settings.database_url)

engine = create_async_engine(settings.database_url, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
