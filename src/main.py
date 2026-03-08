from fastapi import FastAPI

from src.api.routers.auth import router as auth_router
from src.api.routers.base import router as base_router

app = FastAPI()
app.include_router(base_router)
app.include_router(auth_router)
