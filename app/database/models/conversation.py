from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)

    role: Mapped[str] = mapped_column(String(20))  # user | assistant | system
    text: Mapped[str] = mapped_column(Text)

    intent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    promotion_slug: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
