from uuid import UUID

from pydantic import BaseModel, field_validator


class RegisterRequest(BaseModel):
    username: str
    password: str

    @classmethod
    @field_validator("username")
    def validate_username(cls, value: str) -> str:
        value = value.strip()
        if " " in value:
            raise ValueError("Username must not contain spaces")
        return value

    @classmethod
    @field_validator("password")
    def validate_username(cls, value: str) -> str:
        value = value.strip()
        if " " in value:
            raise ValueError("Password must not contain spaces")
        return value


class LoginRequest(BaseModel):
    username: str
    password: str

    @classmethod
    @field_validator("username")
    def validate_username(cls, value: str) -> str:
        value = value.strip()
        if " " in value:
            raise ValueError("Username must not contain spaces")
        return value

    @classmethod
    @field_validator("password")
    def validate_username(cls, value: str) -> str:
        value = value.strip()
        if " " in value:
            raise ValueError("Password must not contain spaces")
        return value


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class UserResponse(BaseModel):
    id: UUID
    username: str
