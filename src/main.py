from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User
from src.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair, UserResponse
from src.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password

app = FastAPI()
bearer_scheme = HTTPBearer(auto_error=False)


@app.get('/')
async def root() -> dict[str, str]:
    return {'message': 'Hello World'}


@app.get('/hello/{name}')
async def say_hello(name: str) -> dict[str, str]:
    return {'message': f'Hello {name}'}


async def _get_user_by_username(db: AsyncSession, username: str) -> User | None:
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()


def _build_token_pair(username: str) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(username),
        refresh_token=create_refresh_token(username),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing access token')

    username = decode_token(credentials.credentials, expected_type='access')
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired access token')

    user = await _get_user_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')

    return user


@app.post('/register', response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    existing_user = await _get_user_by_username(db, payload.username)
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Username already exists')

    user = User(username=payload.username, password=hash_password(payload.password))
    db.add(user)
    await db.commit()

    return _build_token_pair(user.username)


@app.post('/login', response_model=TokenPair)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    user = await _get_user_by_username(db, payload.username)
    if user is None or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid username or password')

    return _build_token_pair(user.username)


@app.post('/refresh', response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    username = decode_token(payload.refresh_token, expected_type='refresh')
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired refresh token')

    user = await _get_user_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')

    return _build_token_pair(user.username)


@app.get('/me', response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=current_user.id, username=current_user.username)
