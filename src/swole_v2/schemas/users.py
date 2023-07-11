from __future__ import annotations

from pydantic import BaseModel, EmailStr, field_validator

from ..dependencies.passwords import pwd_context
from .validators import check_empty_string, schema_validator


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr | None = None

    _check_empty_username = schema_validator("username")(check_empty_string("username"))
    _check_empty_password = schema_validator("password")(check_empty_string("password"))

    @field_validator("password")
    def hash_password(cls, value: str | None) -> str | None:
        return value if value is None else pwd_context.hash(value)
