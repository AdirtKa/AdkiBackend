from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    deck_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("decks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    front_main_text: Mapped[str] = mapped_column(Text, nullable=False)
    front_sub_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    back_main_text: Mapped[str] = mapped_column(Text, nullable=False)
    back_sub_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    front_image_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media_files.id", ondelete="SET NULL"),
        nullable=True,
    )
    front_audio_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media_files.id", ondelete="SET NULL"),
        nullable=True,
    )
    back_image_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media_files.id", ondelete="SET NULL"),
        nullable=True,
    )
    back_audio_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media_files.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    front_image = relationship("MediaFile", foreign_keys=[front_image_id])
    front_audio = relationship("MediaFile", foreign_keys=[front_audio_id])
    back_image = relationship("MediaFile", foreign_keys=[back_image_id])
    back_audio = relationship("MediaFile", foreign_keys=[back_audio_id])

    progress = relationship(
        "CardProgress",
        back_populates="card",
        cascade="all, delete-orphan",
    )
