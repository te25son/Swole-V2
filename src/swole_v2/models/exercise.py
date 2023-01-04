from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import validator
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from . import Workout, User

from ..database.validators import check_empty_string, check_is_uuid
from ..models.links import WorkoutExerciseLink


class ExerciseDetail(SQLModel):
    exercise_id: UUID

    _check_id = validator("exercise_id", allow_reuse=True, pre=True)(check_is_uuid)


class ExerciseCreate(SQLModel):
    name: str

    _check_empty_name = validator("name", allow_reuse=True)(check_empty_string("name"))


class Exercise(SQLModel, table=True):  # type: ignore
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)

    user_id: UUID = Field(foreign_key="user.id")
    user: "User" = Relationship(back_populates="exercises")

    workouts: list["Workout"] = Relationship(
        back_populates="exercises",
        link_model=WorkoutExerciseLink,
        sa_relationship_kwargs=dict(
            primaryjoin="and_(Exercise.id==WorkoutExerciseLink.exercise_id, Exercise.user_id==WorkoutExerciseLink.exercise_user_id)",
            secondaryjoin="and_(Workout.id==WorkoutExerciseLink.workout_id, Workout.user_id==WorkoutExerciseLink.workout_user_id)",
        ),
    )

    __table_args__ = (UniqueConstraint("user_id", "name", name="user_id_and_name_uc"),)


class ExerciseRead(SQLModel):
    name: str
