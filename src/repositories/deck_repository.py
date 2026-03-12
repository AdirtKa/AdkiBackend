from uuid import UUID

from sqlalchemy import select, delete, update
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


async def delete_deck(db: AsyncSession, deck_id: UUID) -> bool:
    deck = await db.get(Deck, deck_id)
    if deck is not None:
        await db.delete(deck)
        await db.commit()
        return True

    return False


async def rename_deck(db: AsyncSession, deck_id: UUID, new_name: str) -> Deck | None:
    deck: Deck | None = await db.get(Deck, deck_id)
    if not deck:
        return None

    deck.name = new_name
    await db.commit()


    await db.refresh(deck)
    return deck
