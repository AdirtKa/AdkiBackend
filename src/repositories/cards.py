from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import and_, case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.card import Card
from src.models.card_progress import CardProgress
from src.models.deck import Deck
from src.models.media_file import MediaFile
from src.models.review_event import ReviewEvent
from src.schemas.card import CardCreate, CardProgressUpdate, CardUpdate


class CardsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _validate_media_refs(
            self,
            *,
            front_image_id: uuid.UUID | None,
            front_audio_id: uuid.UUID | None,
            back_image_id: uuid.UUID | None,
            back_audio_id: uuid.UUID | None,
    ) -> None:
        refs = {
            "front_image_id": front_image_id,
            "front_audio_id": front_audio_id,
            "back_image_id": back_image_id,
            "back_audio_id": back_audio_id,
        }

        ids = [value for value in refs.values() if value is not None]
        if not ids:
            return

        result = await self.session.execute(
            select(MediaFile).where(MediaFile.id.in_(ids))
        )
        media_items = {item.id: item for item in result.scalars().all()}

        for field_name, media_id in refs.items():
            if media_id is None:
                continue

            media = media_items.get(media_id)
            if media is None:
                raise ValueError(f"{field_name}: media file not found")

            if field_name.endswith("image_id") and not media.content_type.startswith("image/"):
                raise ValueError(f"{field_name}: must reference an image")
            if field_name.endswith("audio_id") and not media.content_type.startswith("audio/"):
                raise ValueError(f"{field_name}: must reference an audio file")

    def _stats_base_stmt(self, *, user_id: uuid.UUID, deck_id: uuid.UUID | None = None):
        stmt = (
            select()
            .select_from(Card)
            .join(Deck, Deck.id == Card.deck_id)
            .outerjoin(
                CardProgress,
                and_(
                    CardProgress.card_id == Card.id,
                    CardProgress.user_id == user_id,
                ),
            )
            .where(Deck.owner_id == user_id)
        )

        if deck_id is not None:
            stmt = stmt.where(Deck.id == deck_id)

        return stmt

    async def deck_exists_for_user(self, deck_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(Deck.id).where(Deck.id == deck_id, Deck.owner_id == user_id)
        )
        return result.scalar_one_or_none() is not None

    async def create_card(self, data: CardCreate, user_id) -> Card:
        await self._validate_media_refs(
            front_image_id=data.front_image_id,
            front_audio_id=data.front_audio_id,
            back_image_id=data.back_image_id,
            back_audio_id=data.back_audio_id,
        )

        card = Card(
            deck_id=data.deck_id,
            front_main_text=data.front_main_text,
            front_sub_text=data.front_sub_text,
            back_main_text=data.back_main_text,
            back_sub_text=data.back_sub_text,
            front_image_id=data.front_image_id,
            front_audio_id=data.front_audio_id,
            back_image_id=data.back_image_id,
            back_audio_id=data.back_audio_id,
        )

        self.session.add(card)
        await self.session.flush()

        progress = CardProgress(card_id=card.id, user_id=user_id)
        self.session.add(progress)

        await self.session.commit()

        return await self.get_card(card.id)

    async def get_card(self, card_id: uuid.UUID) -> Card | None:
        result = await self.session.execute(
            select(Card)
            .options(selectinload(Card.progress))
            .where(Card.id == card_id)
        )
        return result.scalar_one_or_none()

    async def list_cards(
            self,
            *,
            deck_id: uuid.UUID | None = None,
            limit: int = 50,
            offset: int = 0,
    ) -> list[Card]:
        stmt = select(Card).options(selectinload(Card.progress)).offset(offset).limit(limit)

        if deck_id is not None:
            stmt = stmt.where(Card.deck_id == deck_id)

        stmt = stmt.order_by(Card.created_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_card(self, card_id: uuid.UUID, data: CardUpdate) -> Card | None:
        card = await self.get_card(card_id)
        if card is None:
            return None

        update_data = data.model_dump(exclude_unset=True)

        await self._validate_media_refs(
            front_image_id=update_data.get("front_image_id", card.front_image_id),
            front_audio_id=update_data.get("front_audio_id", card.front_audio_id),
            back_image_id=update_data.get("back_image_id", card.back_image_id),
            back_audio_id=update_data.get("back_audio_id", card.back_audio_id),
        )

        for field, value in update_data.items():
            setattr(card, field, value)

        await self.session.commit()
        return await self.get_card(card.id)

    async def delete_card(self, card_id: uuid.UUID) -> bool:
        card = await self.get_card(card_id)
        if card is None:
            return False

        await self.session.delete(card)
        await self.session.commit()
        return True

    async def get_progress(self, card_id: uuid.UUID, user_id: uuid.UUID) -> CardProgress | None:
        result = await self.session.execute(
            select(CardProgress).where(CardProgress.card_id == card_id, CardProgress.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_progress(
            self,
            card_id: uuid.UUID,
            user_id: uuid.UUID,
            data: CardProgressUpdate,
    ) -> CardProgress | None:
        progress = await self.get_progress(card_id, user_id)
        if progress is None:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(progress, field, value)

        await self.session.commit()
        await self.session.refresh(progress)
        return progress

    async def get_deck_card_stats(self, deck_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, int] | None:
        deck_exists_stmt = select(Deck.id).where(Deck.id == deck_id, Deck.owner_id == user_id)
        deck_exists = await self.session.execute(deck_exists_stmt)
        if deck_exists.scalar_one_or_none() is None:
            return None

        stmt = (
            select(
                func.count(Card.id).filter(CardProgress.last_answered_at.is_(None)).label("not_studied"),
                func.count(Card.id)
                .filter(CardProgress.last_answered_at.is_not(None), CardProgress.last_answer_correct.is_(True))
                .label("answered_correctly"),
                func.count(Card.id)
                .filter(CardProgress.last_answered_at.is_not(None), CardProgress.last_answer_correct.is_(False))
                .label("answered_incorrectly"),
            )
            .select_from(Card)
            .join(
                CardProgress,
                (CardProgress.card_id == Card.id) & (CardProgress.user_id == user_id),
            )
            .where(Card.deck_id == deck_id)
        )

        result = await self.session.execute(stmt)
        row = result.one()
        return {
            "not_studied": row.not_studied or 0,
            "answered_correctly": row.answered_correctly or 0,
            "answered_incorrectly": row.answered_incorrectly or 0,
        }

    async def get_stats_overview(self, *, user_id: uuid.UUID, deck_id: uuid.UUID | None = None) -> dict[str, int]:
        now = datetime.now(timezone.utc)
        stmt = self._stats_base_stmt(user_id=user_id, deck_id=deck_id).with_only_columns(
            func.count(distinct(Deck.id)).label("deck_count"),
            func.count(Card.id).label("card_count"),
            func.sum(case((CardProgress.last_answered_at.is_not(None), 1), else_=0)).label("reviewed_cards"),
            func.sum(case((CardProgress.last_answered_at.is_(None), 1), else_=0)).label("new_cards"),
            func.sum(
                case(
                    (
                        and_(
                            CardProgress.last_answered_at.is_not(None),
                            CardProgress.interval_days < 7,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("learning_cards"),
            func.sum(case((CardProgress.interval_days >= 7, 1), else_=0)).label("mastered_cards"),
            func.sum(case((CardProgress.due_at <= now, 1), else_=0)).label("due_now"),
            func.sum(case((CardProgress.last_answer_correct.is_(True), 1), else_=0)).label("correct_cards"),
            func.sum(case((CardProgress.last_answer_correct.is_(False), 1), else_=0)).label("incorrect_cards"),
        )

        row = (await self.session.execute(stmt)).one()
        return {
            "deck_count": row.deck_count or 0,
            "card_count": row.card_count or 0,
            "reviewed_cards": row.reviewed_cards or 0,
            "new_cards": row.new_cards or 0,
            "learning_cards": row.learning_cards or 0,
            "mastered_cards": row.mastered_cards or 0,
            "due_now": row.due_now or 0,
            "correct_cards": row.correct_cards or 0,
            "incorrect_cards": row.incorrect_cards or 0,
        }

    async def get_last_review_activity(
            self,
            *,
            user_id: uuid.UUID,
            days: int,
            deck_id: uuid.UUID | None = None,
    ) -> list[dict[str, int | date]]:
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days - 1)

        review_date = func.date(CardProgress.last_answered_at)
        stmt = (
            self._stats_base_stmt(user_id=user_id, deck_id=deck_id)
            .with_only_columns(
                review_date.label("date"),
                func.count(Card.id).label("total"),
                func.sum(case((CardProgress.last_answer_correct.is_(True), 1), else_=0)).label("correct"),
                func.sum(case((CardProgress.last_answer_correct.is_(False), 1), else_=0)).label("incorrect"),
            )
            .where(CardProgress.last_answered_at.is_not(None))
            .where(review_date >= start_date)
            .group_by(review_date)
            .order_by(review_date)
        )

        rows = (await self.session.execute(stmt)).all()
        by_day = {
            row.date: {
                "date": row.date,
                "total": row.total or 0,
                "correct": row.correct or 0,
                "incorrect": row.incorrect or 0,
            }
            for row in rows
        }

        return self._fill_daily_series(
            start_date=start_date,
            days=days,
            raw=by_day,
            empty_factory=lambda current_date: {
                "date": current_date,
                "total": 0,
                "correct": 0,
                "incorrect": 0,
            },
        )

    async def get_review_history(
            self,
            *,
            user_id: uuid.UUID,
            days: int,
            deck_id: uuid.UUID | None = None,
    ) -> list[dict[str, int | float | date]]:
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days - 1)

        reviewed_date = func.date(ReviewEvent.reviewed_at)
        stmt = (
            select(
                reviewed_date.label("date"),
                func.count(ReviewEvent.id).label("total_reviews"),
                func.sum(case((ReviewEvent.was_correct.is_(True), 1), else_=0)).label("correct_reviews"),
                func.sum(case((ReviewEvent.was_correct.is_(False), 1), else_=0)).label("incorrect_reviews"),
                func.avg(ReviewEvent.quality).label("average_quality"),
            )
            .select_from(ReviewEvent)
            .join(Card, Card.id == ReviewEvent.card_id)
            .join(Deck, Deck.id == Card.deck_id)
            .where(ReviewEvent.user_id == user_id)
            .where(Deck.owner_id == user_id)
            .where(reviewed_date >= start_date)
        )

        if deck_id is not None:
            stmt = stmt.where(Deck.id == deck_id)

        stmt = stmt.group_by(reviewed_date).order_by(reviewed_date)

        rows = (await self.session.execute(stmt)).all()
        by_day = {
            row.date: {
                "date": row.date,
                "total_reviews": row.total_reviews or 0,
                "correct_reviews": row.correct_reviews or 0,
                "incorrect_reviews": row.incorrect_reviews or 0,
                "average_quality": float(row.average_quality or 0),
            }
            for row in rows
        }

        return self._fill_daily_series(
            start_date=start_date,
            days=days,
            raw=by_day,
            empty_factory=lambda current_date: {
                "date": current_date,
                "total_reviews": 0,
                "correct_reviews": 0,
                "incorrect_reviews": 0,
                "average_quality": 0.0,
            },
        )

    async def get_due_forecast(
            self,
            *,
            user_id: uuid.UUID,
            days: int,
            deck_id: uuid.UUID | None = None,
    ) -> list[dict[str, int | date]]:
        start_date = datetime.now(timezone.utc).date()
        end_date = start_date + timedelta(days=days - 1)

        due_date = func.date(CardProgress.due_at)
        stmt = (
            self._stats_base_stmt(user_id=user_id, deck_id=deck_id)
            .with_only_columns(
                due_date.label("date"),
                func.count(Card.id).label("due_cards"),
            )
            .where(CardProgress.due_at.is_not(None))
            .where(due_date >= start_date)
            .where(due_date <= end_date)
            .group_by(due_date)
            .order_by(due_date)
        )

        rows = (await self.session.execute(stmt)).all()
        by_day = {
            row.date: {
                "date": row.date,
                "due_cards": row.due_cards or 0,
            }
            for row in rows
        }

        return self._fill_daily_series(
            start_date=start_date,
            days=days,
            raw=by_day,
            empty_factory=lambda current_date: {
                "date": current_date,
                "due_cards": 0,
            },
        )

    async def get_decks_progress(self, *, user_id: uuid.UUID) -> list[dict[str, int | str | uuid.UUID]]:
        now = datetime.now(timezone.utc)
        stmt = (
            self._stats_base_stmt(user_id=user_id)
            .with_only_columns(
                Deck.id.label("deck_id"),
                Deck.name.label("deck_name"),
                func.count(Card.id).label("total_cards"),
                func.sum(case((CardProgress.last_answered_at.is_(None), 1), else_=0)).label("new_cards"),
                func.sum(
                    case(
                        (
                            and_(
                                CardProgress.last_answered_at.is_not(None),
                                CardProgress.interval_days < 7,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("learning_cards"),
                func.sum(case((CardProgress.interval_days >= 7, 1), else_=0)).label("mastered_cards"),
                func.sum(case((CardProgress.due_at <= now, 1), else_=0)).label("due_cards"),
            )
            .group_by(Deck.id, Deck.name)
            .order_by(Deck.name.asc())
        )

        rows = (await self.session.execute(stmt)).all()
        return [
            {
                "deck_id": row.deck_id,
                "deck_name": row.deck_name,
                "total_cards": row.total_cards or 0,
                "new_cards": row.new_cards or 0,
                "learning_cards": row.learning_cards or 0,
                "mastered_cards": row.mastered_cards or 0,
                "due_cards": row.due_cards or 0,
            }
            for row in rows
        ]

    @staticmethod
    def _fill_daily_series(
            *,
            start_date: date,
            days: int,
            raw: dict[date, dict[str, int | float | date]],
            empty_factory,
    ) -> list[dict[str, int | float | date]]:
        result: list[dict[str, int | float | date]] = []
        for offset in range(days):
            current_date = start_date + timedelta(days=offset)
            result.append(raw.get(current_date, empty_factory(current_date)))
        return result
