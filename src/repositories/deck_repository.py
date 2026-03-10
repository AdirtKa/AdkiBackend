from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.deck import Deck


async def get_user_decks(db: AsyncSession, user_id: UUID) -> list[Deck]:
    query = select(Deck).where(Deck.owner_id == user_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_deck(db: AsyncSession, deck_name: str, user_id: UUID) -> Deck:
    deck = Deck(name=deck_name, owner_id=user_id)
    db.add(deck)
    await db.commit()
    await db.refresh(deck)
    return deck