from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import validator
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .workout import Workout

from ..database.validators import check_is_uuid
from .links import WorkoutExerciseLink


class ExerciseGetAll(SQLModel):
    workout_id: UUID

    _check_id = validator("workout_id", allow_reuse=True, pre=True)(check_is_uuid)


class ExerciseDetail(SQLModel):
    exercise_id: UUID

    _check_id = validator("exercise_id", allow_reuse=True, pre=True)(check_is_uuid)


class Exercise(SQLModel, table=True):  # type: ignore
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)

    workouts: list["Workout"] = Relationship(back_populates="exercises", link_model=WorkoutExerciseLink)


class ExerciseRead(SQLModel):
    name: str
