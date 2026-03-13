from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.models import User
from src.repositories.cards import CardsRepository
from src.schemas.card import (
    CardCreate,
    CardProgressResponse,
    CardProgressUpdate,
    CardResponse,
    CardUpdate,
    StudyCardResponse,
)

router = APIRouter(prefix="/cards", tags=["cards"])


def build_media_url(media_id: uuid.UUID | None) -> str | None:
    return f"/media/{media_id}" if media_id else None


def to_card_response(card) -> CardResponse:
    return CardResponse(
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
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


def to_study_card_response(card, progress) -> StudyCardResponse:
    return StudyCardResponse(
        card=to_card_response(card),
        progress=CardProgressResponse.model_validate(progress),
    )


@router.post("/", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
        payload: CardCreate,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    repo = CardsRepository(session)

    try:
        card = await repo.create_card(payload, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return to_card_response(card)


@router.get("/", response_model=list[CardResponse])
async def list_cards(
        deck_id: uuid.UUID | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        session: AsyncSession = Depends(get_db),
):
    repo = CardsRepository(session)
    cards = await repo.list_cards(deck_id=deck_id, limit=limit, offset=offset)
    return [to_card_response(card) for card in cards]


@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
        card_id: uuid.UUID,
        session: AsyncSession = Depends(get_db),
):
    repo = CardsRepository(session)
    card = await repo.get_card(card_id)

    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    return to_card_response(card)


@router.put("/{card_id}", response_model=CardResponse)
async def update_card(
        card_id: uuid.UUID,
        payload: CardUpdate,
        session: AsyncSession = Depends(get_db),
):
    repo = CardsRepository(session)

    try:
        card = await repo.update_card(card_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    return to_card_response(card)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
        card_id: uuid.UUID,
        session: AsyncSession = Depends(get_db),
):
    repo = CardsRepository(session)
    deleted = await repo.delete_card(card_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Card not found")


@router.get("/{card_id}/progress", response_model=CardProgressResponse)
async def get_card_progress(
        card_id: uuid.UUID,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    repo = CardsRepository(session)
    progress = await repo.get_progress(card_id, current_user.id)

    if progress is None:
        raise HTTPException(status_code=404, detail="Progress not found")

    return CardProgressResponse.model_validate(progress)


@router.patch("/{card_id}/progress", response_model=CardProgressResponse)
async def update_card_progress(
        card_id: uuid.UUID,
        payload: CardProgressUpdate,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    repo = CardsRepository(session)
    progress = await repo.update_progress(card_id, current_user.id, payload)

    if progress is None:
        raise HTTPException(status_code=404, detail="Progress not found")

    return CardProgressResponse.model_validate(progress)


@router.get("/{card_id}/study", response_model=StudyCardResponse)
async def get_study_card(
        card_id: uuid.UUID,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    repo = CardsRepository(session)

    card = await repo.get_card(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    progress = await repo.get_progress(card_id, current_user.id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Progress not found")

    return to_study_card_response(card, progress)
