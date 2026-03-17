from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel


class UserStatsOverviewResponse(BaseModel):
    deck_count: int
    card_count: int
    reviewed_cards: int
    new_cards: int
    learning_cards: int
    mastered_cards: int
    due_now: int
    correct_cards: int
    incorrect_cards: int


class ReviewActivityPointResponse(BaseModel):
    date: date
    total: int
    correct: int
    incorrect: int


class ReviewHistoryPointResponse(BaseModel):
    date: date
    total_reviews: int
    correct_reviews: int
    incorrect_reviews: int
    average_quality: float


class DueForecastPointResponse(BaseModel):
    date: date
    due_cards: int


class DeckProgressStatsResponse(BaseModel):
    deck_id: uuid.UUID
    deck_name: str
    total_cards: int
    new_cards: int
    learning_cards: int
    mastered_cards: int
    due_cards: int
