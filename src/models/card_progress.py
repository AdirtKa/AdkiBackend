from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class CardProgress(Base):
    __tablename__ = "card_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "card_id", name="uq_card_progress_user_card"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ease: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    repetitions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_answer_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    card = relationship("Card", back_populates="progress")
    user = relationship("User")
