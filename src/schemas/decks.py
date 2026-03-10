from pydantic import BaseModel
from uuid import UUID


class DeckCreate(BaseModel):
    name: str

class DeckRead(BaseModel):
    id: UUID
    name: str