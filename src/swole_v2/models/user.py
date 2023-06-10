from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: UUID | None
    username: str | None
    hashed_password: str | None
    email: EmailStr | None
    disabled: bool | None


class UserRead(BaseModel):
    id: UUID
    username: str
    disabled: bool | None
    email: EmailStr | None
