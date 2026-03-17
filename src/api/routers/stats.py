from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.models.user import User
from src.repositories.cards import CardsRepository
from src.schemas.stats import (
    DeckProgressStatsResponse,
    DueForecastPointResponse,
    ReviewActivityPointResponse,
    ReviewHistoryPointResponse,
    UserStatsOverviewResponse,
)

router = APIRouter(prefix="/stats", tags=["stats"])


async def _ensure_deck_access(
    repo: CardsRepository,
    *,
    user_id: uuid.UUID,
    deck_id: uuid.UUID | None,
) -> None:
    if deck_id is None:
        return

    if not await repo.deck_exists_for_user(deck_id, user_id):
        raise HTTPException(status_code=404, detail="Deck not found")


@router.get("/overview", response_model=UserStatsOverviewResponse)
async def get_stats_overview(
    deck_id: uuid.UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = CardsRepository(session)
    await _ensure_deck_access(repo, user_id=current_user.id, deck_id=deck_id)
    stats = await repo.get_stats_overview(user_id=current_user.id, deck_id=deck_id)
    return UserStatsOverviewResponse(**stats)


@router.get("/last-review-activity", response_model=list[ReviewActivityPointResponse])
async def get_last_review_activity(
    deck_id: uuid.UUID | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = CardsRepository(session)
    await _ensure_deck_access(repo, user_id=current_user.id, deck_id=deck_id)
    rows = await repo.get_last_review_activity(
        user_id=current_user.id,
        deck_id=deck_id,
        days=days,
    )
    return [ReviewActivityPointResponse(**row) for row in rows]


@router.get("/review-history", response_model=list[ReviewHistoryPointResponse])
async def get_review_history(
    deck_id: uuid.UUID | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = CardsRepository(session)
    await _ensure_deck_access(repo, user_id=current_user.id, deck_id=deck_id)
    rows = await repo.get_review_history(
        user_id=current_user.id,
        deck_id=deck_id,
        days=days,
    )
    return [ReviewHistoryPointResponse(**row) for row in rows]


@router.get("/due-forecast", response_model=list[DueForecastPointResponse])
async def get_due_forecast(
    deck_id: uuid.UUID | None = Query(default=None),
    days: int = Query(default=14, ge=1, le=90),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = CardsRepository(session)
    await _ensure_deck_access(repo, user_id=current_user.id, deck_id=deck_id)
    rows = await repo.get_due_forecast(
        user_id=current_user.id,
        deck_id=deck_id,
        days=days,
    )
    return [DueForecastPointResponse(**row) for row in rows]


@router.get("/decks/progress", response_model=list[DeckProgressStatsResponse])
async def get_deck_progress(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = CardsRepository(session)
    rows = await repo.get_decks_progress(user_id=current_user.id)
    return [DeckProgressStatsResponse(**row) for row in rows]
