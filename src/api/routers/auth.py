from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.models.user import User
from src.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair, UserResponse
from src.services.auth_service import login_user, refresh_tokens, register_user

router = APIRouter(tags=['auth'])


@router.post('/register', response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    return await register_user(db, payload.username, payload.password)


@router.post('/login', response_model=TokenPair)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    return await login_user(db, payload.username, payload.password)


@router.post('/refresh', response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    return await refresh_tokens(db, payload.refresh_token)


@router.get('/me', response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=current_user.id, username=current_user.username)
