from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.repositories.user_repository import create_user, get_user_by_username
from src.schemas.auth import TokenPair
from src.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password


def build_token_pair(username: str) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(username),
        refresh_token=create_refresh_token(username),
    )


async def register_user(db: AsyncSession, username: str, password: str) -> TokenPair:
    existing_user = await get_user_by_username(db, username)
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Username already exists')

    user = await create_user(db, username, hash_password(password))
    return build_token_pair(user.username)


async def login_user(db: AsyncSession, username: str, password: str) -> TokenPair:
    user = await get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid username or password')

    return build_token_pair(user.username)


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenPair:
    username = decode_token(refresh_token, expected_type='refresh')
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired refresh token')

    user = await get_user_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')

    return build_token_pair(user.username)


async def get_user_from_access_token(db: AsyncSession, access_token: str) -> User:
    username = decode_token(access_token, expected_type='access')
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired access token')

    user = await get_user_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')

    return user
