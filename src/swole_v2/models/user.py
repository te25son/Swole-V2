from uuid import UUID

from pydantic import BaseModel, EmailStr


class User(BaseModel):  # type: ignore
    id: UUID | None
    username: str | None
    hashed_password: str | None
    email: EmailStr | None
    disabled: bool | None


class UserRead(BaseModel):
    username: str | None
    email: EmailStr | None
