import datetime as dt
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from . import User, WorkoutExerciseLink


class Workout(SQLModel, table=True):  # type: ignore
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    date: dt.date = Field(index=True)

    user_id: UUID = Field(foreign_key="user.id")
    user: "User" = Relationship(back_populates="workouts")

    exercise_links: list["WorkoutExerciseLink"] = Relationship(
        back_populates="workout",
        sa_relationship_kwargs=dict(
            primaryjoin="and_(Workout.id==WorkoutExerciseLink.workout_id, Workout.user_id==WorkoutExerciseLink.workout_user_id)",
            cascade="all, delete-orphan",
        ),
    )

    __table_args__ = (
        Index("search_workout_by_id_and_user_id", "id", "user_id"),
        UniqueConstraint("user_id", "name", "date", name="name_date_user_id_uc"),
    )


class WorkoutRead(SQLModel):
    name: str
    date: dt.date
