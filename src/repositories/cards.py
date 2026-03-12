from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.card import Card
from src.models.card_progress import CardProgress
from src.models.deck import Deck
from src.models.media_file import MediaFile
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
