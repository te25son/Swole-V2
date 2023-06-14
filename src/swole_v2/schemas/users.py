from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, validator

from ..dependencies.passwords import pwd_context
from .validators import check_empty_string, check_is_uuid, schema_validator


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr | None

    _check_empty_username = schema_validator("username")(check_empty_string("username"))
    _check_empty_password = schema_validator("password")(check_empty_string("password"))

    @validator("password")
    def hash_password(cls, value: str | None) -> str | None:
        return value if value is None else pwd_context.hash(value)


class UserDelete(BaseModel):
    user_id: UUID

    _check_id = schema_validator("user_id")(check_is_uuid)
