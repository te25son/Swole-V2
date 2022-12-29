from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .workout import Workout


class User(SQLModel, table=True):  # type: ignore
    id: UUID | None = Field(primary_key=True, default_factory=uuid4, index=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    email: EmailStr | None = None
    full_name: str | None = None
    disabled: bool | None = False

    workouts: list["Workout"] = Relationship(back_populates="user")


class UserRead(SQLModel):
    username: str
    email: EmailStr | None = None
    full_name: str | None = None
