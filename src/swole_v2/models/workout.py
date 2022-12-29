import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User
    from .exercise import Exercise

from .links import WorkoutExerciseLink


class Workout(SQLModel, table=True):  # type: ignore
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True, min_length=1)
    date: datetime.date = Field(index=True)

    user_id: UUID = Field(..., foreign_key="user.id")
    user: "User" = Relationship(back_populates="workouts")

    exercises: list["Exercise"] = Relationship(back_populates="workouts", link_model=WorkoutExerciseLink)

    __table_args__ = (UniqueConstraint("name", "date", name="name_date_uc"),)


class WorkoutRead(SQLModel):
    name: str
    date: datetime.date


class WorkoutCreate(SQLModel):
    name: str
    date: datetime.date


class WorkoutUpdate(SQLModel):
    name: str | None = None
    date: datetime.date | None = None
