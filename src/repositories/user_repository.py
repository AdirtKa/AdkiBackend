from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, username: str, password_hash: str) -> User:
    user = User(username=username, password=password_hash)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
