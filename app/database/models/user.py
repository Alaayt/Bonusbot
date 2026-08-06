import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PlayerStage(str, enum.Enum):
    NEW = "new"
    EXPLORING = "exploring"
    SPORTS_INTERESTED = "sports_interested"
    CASINO_INTERESTED = "casino_interested"
    SEEKING_BONUS = "seeking_bonus"
    NEEDS_EXPLANATION = "needs_explanation"
    HAS_OBJECTION = "has_objection"
    READY_TO_REGISTER = "ready_to_register"
    ALREADY_REGISTERED = "already_registered"
    NEEDS_POST_SIGNUP_HELP = "needs_post_signup_help"
    NEEDS_HUMAN_MANAGER = "needs_human_manager"
    INELIGIBLE = "ineligible"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    language: Mapped[str | None] = mapped_column(String(5), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(5), nullable=True)

    age_confirmed_adult: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_minor_flagged: Mapped[bool] = mapped_column(Boolean, default=False)

    has_existing_account: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    used_promo_code_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    stage: Mapped[PlayerStage] = mapped_column(Enum(PlayerStage), default=PlayerStage.NEW)

    marketing_opt_out: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
