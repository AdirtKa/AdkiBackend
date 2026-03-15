from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User
from src.repositories.review import ReviewRepository
from src.schemas.review import (
    CardProgressResponse,
    ReviewAnswerRequest,
    ReviewCardResponse,
)
from src.dependencies.auth import get_current_user

router = APIRouter(prefix="/review", tags=["review"])


def build_media_url(media_id: uuid.UUID | None) -> str | None:
    return f"/media/{media_id}" if media_id else None


def to_review_card_response(card, progress) -> ReviewCardResponse:
    return ReviewCardResponse(
        id=card.id,
        deck_id=card.deck_id,
        front_main_text=card.front_main_text,
        front_sub_text=card.front_sub_text,
        back_main_text=card.back_main_text,
        back_sub_text=card.back_sub_text,
        front_image_id=card.front_image_id,
        front_audio_id=card.front_audio_id,
        back_image_id=card.back_image_id,
        back_audio_id=card.back_audio_id,
        front_image_url=build_media_url(card.front_image_id),
        front_audio_url=build_media_url(card.front_audio_id),
        back_image_url=build_media_url(card.back_image_id),
        back_audio_url=build_media_url(card.back_audio_id),
        progress=CardProgressResponse.model_validate(progress),
    )


@router.get("/due", response_model=list[ReviewCardResponse])
async def get_due_cards(
    deck_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ReviewRepository(db)
    rows = await repo.list_due_cards_including_new(
        user_id=current_user.id,
        deck_id=deck_id,
        limit=limit,
        offset=offset,
    )
    return [to_review_card_response(card, progress) for card, progress in rows]


@router.post("/cards/{card_id}/answer", response_model=CardProgressResponse)
async def answer_card(
    card_id: uuid.UUID,
    payload: ReviewAnswerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ReviewRepository(db)
    progress = await repo.answer_card(
        user_id=current_user.id,
        card_id=card_id,
        quality=payload.quality,
    )

    if progress is None:
        raise HTTPException(status_code=404, detail="Card not found")

    return CardProgressResponse.model_validate(progress)