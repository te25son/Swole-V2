import datetime as dt
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from . import User, Exercise

from ..models.links import WorkoutExerciseLink


class Workout(SQLModel, table=True):  # type: ignore
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    date: dt.date = Field(index=True)

    user_id: UUID = Field(foreign_key="user.id")
    user: "User" = Relationship(back_populates="workouts")

    exercises: list["Exercise"] = Relationship(
        back_populates="workouts",
        link_model=WorkoutExerciseLink,
        sa_relationship_kwargs=dict(
            primaryjoin="and_(Workout.id==WorkoutExerciseLink.workout_id, Workout.user_id==WorkoutExerciseLink.workout_user_id)",
            secondaryjoin="and_(Exercise.id==WorkoutExerciseLink.exercise_id, Exercise.user_id==WorkoutExerciseLink.exercise_user_id)",
        ),
    )

    __table_args__ = (UniqueConstraint("user_id", "name", "date", name="name_date_user_id_uc"),)


class WorkoutRead(SQLModel):
    name: str
    date: dt.date
