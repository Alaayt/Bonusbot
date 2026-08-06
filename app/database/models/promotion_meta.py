from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PromotionOverride(Base):
    """تعديلات لوحة الإدارة فوق ملفات JSON الأساسية (بدون الكتابة المباشرة على الملفات وقت التشغيل)."""

    __tablename__ = "promotion_overrides"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    status_override: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source_url_override: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    updated_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PromotionClick(Base):
    __tablename__ = "promotion_clicks"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    slug: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    click_type: Mapped[str] = mapped_column(String(30))  # promotion_view | registration_link | app_download
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PendingUpdate(Base):
    """تحديثات مكتشفة من المجدول (أو مرفوعة يدويًا) تنتظر موافقة المشرف."""

    __tablename__ = "pending_updates"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), index=True)
    old_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30))  # scheduler | admin_upload
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | approved | rejected
    reviewed_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLogEntry(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(String(100))
    target_slug: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ManagerAlert(Base):
    __tablename__ = "manager_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str | None] = mapped_column(String(5), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(5), nullable=True)
    reason: Mapped[str] = mapped_column(String(50))
    promotion_slug: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    handled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AdminCountry(Base):
    """دول إضافية يضيفها المشرف من لوحة الإدارة فوق DEFAULT_SUPPORTED_COUNTRIES."""

    __tablename__ = "admin_countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(5), unique=True)
    name_ar: Mapped[str] = mapped_column(String(100))
    name_en: Mapped[str] = mapped_column(String(100))
    name_fr: Mapped[str] = mapped_column(String(100))
    added_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
