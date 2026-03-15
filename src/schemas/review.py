from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewAnswerRequest(BaseModel):
    quality: int = Field(ge=0, le=4)


class CardProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ease: float
    repetitions: int
    interval_days: int
    last_answered_at: datetime | None
    last_answer_correct: bool | None
    due_at: datetime


class ReviewCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    deck_id: uuid.UUID

    front_main_text: str
    front_sub_text: str | None

    back_main_text: str
    back_sub_text: str | None

    front_image_id: uuid.UUID | None
    front_audio_id: uuid.UUID | None
    back_image_id: uuid.UUID | None
    back_audio_id: uuid.UUID | None

    front_image_url: str | None = None
    front_audio_url: str | None = None
    back_image_url: str | None = None
    back_audio_url: str | None = None

    progress: CardProgressResponse
    