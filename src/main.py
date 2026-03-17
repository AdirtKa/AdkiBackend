from fastapi import FastAPI

from src.api.routers.auth import router as auth_router
from src.api.routers.base import router as base_router
from src.api.routers.decks import router as decks_router
from src.api.routers.media import router as media_router
from src.api.routers.cards import router as cards_router
from src.api.routers.review import router as review_router
from src.api.routers.stats import router as stats_router

app = FastAPI()
app.include_router(base_router)
app.include_router(auth_router, prefix='/auth')
app.include_router(decks_router, prefix='/decks', tags=['decks'])

app.include_router(cards_router)
app.include_router(media_router)
app.include_router(review_router)
app.include_router(stats_router)
