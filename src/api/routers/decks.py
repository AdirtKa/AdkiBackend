from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.models.user import User
from src.schemas.decks import DeckRead, DeckCreate, DeckRename
from src.repositories.deck_repository import create_deck, get_user_decks, delete_deck, rename_deck


router = APIRouter(tags=["decks"])


@router.post("/create", response_model=DeckRead, status_code=status.HTTP_201_CREATED)
async def create(payload: DeckCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await create_deck(db, payload.name, current_user.id)


@router.get("/", response_model=list[DeckRead], status_code=status.HTTP_200_OK)
async def decks(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await get_user_decks(db, current_user.id)


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(deck_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await delete_deck(db, deck_id)


@router.put("/{deck_id}", response_model=DeckRead, status_code=status.HTTP_200_OK)
async def rename(payload: DeckRename, deck_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await rename_deck(db=db, new_name=payload.name, deck_id=deck_id)

