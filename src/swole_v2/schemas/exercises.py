from uuid import UUID

from pydantic import validator
from sqlmodel import SQLModel

from .validators import check_empty_string, check_is_uuid


class ExerciseDetail(SQLModel):
    exercise_id: UUID

    _check_id = validator("exercise_id", allow_reuse=True, pre=True)(check_is_uuid)


class ExerciseCreate(SQLModel):
    name: str

    _check_empty_name = validator("name", allow_reuse=True, pre=True, always=True)(check_empty_string("name"))


class ExerciseAddToWorkout(SQLModel):
    exercise_id: UUID
    workout_id: UUID

    _check_ids = validator("exercise_id", "workout_id", allow_reuse=True, pre=True)(check_is_uuid)


class ExerciseUpdate(SQLModel):
    exercise_id: UUID
    name: str

    _check_ids = validator("exercise_id", allow_reuse=True, pre=True)(check_is_uuid)
    _check_empty_name = validator("name", allow_reuse=True, pre=True, always=True)(check_empty_string("name"))


class ExerciseDelete(SQLModel):
    exercise_id: UUID

    _check_ids = validator("exercise_id", allow_reuse=True, pre=True)(check_is_uuid)
