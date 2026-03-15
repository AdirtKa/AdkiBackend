from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.card import Card
from src.models.card_progress import CardProgress
from src.models.deck import Deck


async def get_user_decks(db: AsyncSession, user_id: UUID) -> list[Deck]:
    query = select(Deck).where(Deck.owner_id == user_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_deck(db: AsyncSession, deck_name: str, user_id: UUID) -> Deck:
    deck = Deck(name=deck_name, owner_id=user_id)
    db.add(deck)
    await db.flush()

    sample_cards: list[Card] = []
    for index in range(1, 6):
        card = Card(
            deck_id=deck.id,
            front_main_text=f"{deck_name} card {index}",
            back_main_text=f"{deck_name} answer {index}",
        )
        db.add(card)
        sample_cards.append(card)

    await db.flush()

    for card in sample_cards:
        db.add(CardProgress(card_id=card.id, user_id=user_id))

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
