from __future__ import annotations

from pydantic import BaseModel, EmailStr, field_validator

from ..dependencies.passwords import pwd_context
from .validators import NonEmptyString


class UserLogin(BaseModel):
    username: NonEmptyString
    password: NonEmptyString


class UserCreate(BaseModel):
    username: NonEmptyString
    password: NonEmptyString
    email: EmailStr | None = None

    @field_validator("password")
    def hash_password(cls, value: str | None) -> str | None:
        return value if value is None else pwd_context.hash(value)
