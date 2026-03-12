from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.repositories.user_repository import create_user, get_user_by_id, get_user_by_username
from src.schemas.auth import TokenPair
from src.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password


_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Invalid username or password',
)
_USER_NOT_FOUND = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='User not found',
)
_INVALID_REFRESH_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Invalid or expired refresh token',
)
_INVALID_ACCESS_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Invalid or expired access token',
)


def build_token_pair(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user.id, user.username),
        refresh_token=create_refresh_token(user.id, user.username),
    )


async def register_user(db: AsyncSession, username: str, password: str) -> TokenPair:
    existing_user = await get_user_by_username(db, username)
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Username already exists')

    user = await create_user(db, username, hash_password(password))
    return build_token_pair(user)


async def login_user(db: AsyncSession, username: str, password: str) -> TokenPair:
    user = await get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        raise _INVALID_CREDENTIALS

    return build_token_pair(user)


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenPair:
    user_id = decode_token(refresh_token, expected_type='refresh')
    if user_id is None:
        raise _INVALID_REFRESH_TOKEN

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise _USER_NOT_FOUND

    return build_token_pair(user)


async def get_user_from_access_token(db: AsyncSession, access_token: str) -> User:
    user_id = decode_token(access_token, expected_type='access')
    if user_id is None:
        raise _INVALID_ACCESS_TOKEN

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise _USER_NOT_FOUND

    return user
