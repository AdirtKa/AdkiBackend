from pydantic import BaseModel


class DeckCreate(BaseModel):
    name: str

class DeckRead(BaseModel):
    id: int
    name: str