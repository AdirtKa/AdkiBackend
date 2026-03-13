from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class MediaUploadResponse(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    url: str
    created_at: datetime


class CardMediaUploadResponse(BaseModel):
    front_image: MediaUploadResponse | None = None
    front_audio: MediaUploadResponse | None = None
    back_image: MediaUploadResponse | None = None
    back_audio: MediaUploadResponse | None = None
