from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: UUID | None = None
    username: str | None = None
    hashed_password: str | None = None
    email: EmailStr | None = None
    disabled: bool | None = None


class UserRead(BaseModel):
    id: UUID
    username: str
    disabled: bool | None = None
    email: EmailStr | None = None
