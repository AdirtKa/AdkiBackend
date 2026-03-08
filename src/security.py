import base64
import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from src.config import settings


def hash_password(password: str) -> str:
    """Generate a salted hash using pbkdf2_hmac."""
    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
    return f"{base64.b64encode(salt).decode()}:{base64.b64encode(password_hash).decode()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored salt:hash format."""
    try:
        salt_b64, hash_b64 = stored_hash.split(':', maxsplit=1)
        salt = base64.b64decode(salt_b64)
        expected_hash = base64.b64decode(hash_b64)
    except (ValueError, TypeError):
        return False

    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
    return hmac.compare_digest(password_hash, expected_hash)


def _create_token(user_id: UUID, username: str, token_type: str, expires_in_seconds: int) -> str:
    now = datetime.now(UTC)
    payload = {
        'sub': str(user_id),
        'username': username,
        'type': token_type,
        'iat': now,
        'exp': now + timedelta(seconds=expires_in_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID, username: str) -> str:
    return _create_token(user_id, username, 'access', settings.jwt_access_expires)


def create_refresh_token(user_id: UUID, username: str) -> str:
    return _create_token(user_id, username, 'refresh', settings.jwt_refresh_expires)


def decode_token(token: str, expected_type: str) -> UUID | None:
    """Decode token and validate token type. Returns user UUID if valid."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError:
        return None

    if payload.get('type') != expected_type:
        return None

    subject = payload.get('sub')
    if not isinstance(subject, str):
        return None

    try:
        return UUID(subject)
    except ValueError:
        return None
