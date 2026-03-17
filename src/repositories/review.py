from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.card import Card
from src.models.card_progress import CardProgress
from src.models.review_event import ReviewEvent
from src.services.srs import apply_srs_answer


class ReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_progress(self, *, user_id: uuid.UUID, card_id: uuid.UUID) -> CardProgress:
        result = await self.session.execute(
            select(CardProgress).where(
                CardProgress.user_id == user_id,
                CardProgress.card_id == card_id,
            )
        )
        progress = result.scalar_one_or_none()

        if progress is not None:
            return progress

        progress = CardProgress(
            user_id=user_id,
            card_id=card_id,
        )
        self.session.add(progress)
        await self.session.flush()
        return progress

    async def answer_card(
        self,
        *,
        user_id: uuid.UUID,
        card_id: uuid.UUID,
        quality: int,
    ) -> CardProgress | None:
        card_exists = await self.session.execute(
            select(Card.id).where(Card.id == card_id)
        )
        if card_exists.scalar_one_or_none() is None:
            return None

        progress = await self.get_or_create_progress(user_id=user_id, card_id=card_id)
        apply_srs_answer(progress, quality)

        self.session.add(
            ReviewEvent(
                user_id=user_id,
                card_id=card_id,
                quality=quality,
                was_correct=quality > 1,
                reviewed_at=progress.last_answered_at,
            )
        )

        await self.session.commit()
        await self.session.refresh(progress)
        return progress

    async def list_due_cards(
        self,
        *,
        user_id: uuid.UUID,
        deck_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[Card, CardProgress]]:
        now = datetime.now(timezone.utc)

        stmt = (
            select(Card, CardProgress)
            .join(
                CardProgress,
                and_(
                    CardProgress.card_id == Card.id,
                    CardProgress.user_id == user_id,
                ),
            )
            .options(selectinload(Card.front_image))
            .options(selectinload(Card.front_audio))
            .options(selectinload(Card.back_image))
            .options(selectinload(Card.back_audio))
            .where(CardProgress.due_at <= now)
            .order_by(CardProgress.due_at.asc())
            .offset(offset)
            .limit(limit)
        )

        if deck_id is not None:
            stmt = stmt.where(Card.deck_id == deck_id)

        result = await self.session.execute(stmt)
        rows = result.all()
        return [(card, progress) for card, progress in rows]

    async def create_missing_progress_for_deck(
        self,
        *,
        user_id: uuid.UUID,
        deck_id: uuid.UUID | None = None,
    ) -> None:
        stmt = select(Card.id)

        if deck_id is not None:
            stmt = stmt.where(Card.deck_id == deck_id)

        cards_result = await self.session.execute(stmt)
        card_ids = list(cards_result.scalars().all())

        if not card_ids:
            return

        existing_result = await self.session.execute(
            select(CardProgress.card_id).where(
                CardProgress.user_id == user_id,
                CardProgress.card_id.in_(card_ids),
            )
        )
        existing_ids = set(existing_result.scalars().all())

        for card_id in card_ids:
            if card_id in existing_ids:
                continue
            self.session.add(
                CardProgress(
                    user_id=user_id,
                    card_id=card_id,
                )
            )

        await self.session.commit()

    async def list_due_cards_including_new(
        self,
        *,
        user_id: uuid.UUID,
        deck_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[Card, CardProgress]]:
        await self.create_missing_progress_for_deck(user_id=user_id, deck_id=deck_id)
        return await self.list_due_cards(
            user_id=user_id,
            deck_id=deck_id,
            limit=limit,
            offset=offset,
        )
