from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CardProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ease: float
    repetitions: int
    interval_days: int
    last_answered_at: datetime | None
    last_answer_correct: bool | None


class CardCreate(BaseModel):
    deck_id: uuid.UUID

    front_main_text: str = Field(min_length=1)
    front_sub_text: str | None = None

    back_main_text: str = Field(min_length=1)
    back_sub_text: str | None = None

    front_image_id: uuid.UUID | None = None
    front_audio_id: uuid.UUID | None = None
    back_image_id: uuid.UUID | None = None
    back_audio_id: uuid.UUID | None = None


class CardUpdate(BaseModel):
    front_main_text: str | None = None
    front_sub_text: str | None = None

    back_main_text: str | None = None
    back_sub_text: str | None = None

    front_image_id: uuid.UUID | None = None
    front_audio_id: uuid.UUID | None = None
    back_image_id: uuid.UUID | None = None
    back_audio_id: uuid.UUID | None = None


class CardProgressUpdate(BaseModel):
    ease: float | None = None
    repetitions: int | None = None
    interval_days: int | None = None
    last_answer_correct: bool | None = None
    last_answered_at: datetime | None = None


class CardResponse(BaseModel):
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

    created_at: datetime
    updated_at: datetime


class StudyCardResponse(BaseModel):
    card: CardResponse
    progress: CardProgressResponse
