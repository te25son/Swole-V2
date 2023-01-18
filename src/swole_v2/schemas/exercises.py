from uuid import UUID

from pydantic import BaseModel

from .validators import check_empty_string, check_is_uuid, schema_validator


class ExerciseDetail(BaseModel):
    exercise_id: UUID

    _check_id = schema_validator("exercise_id")(check_is_uuid)


class ExerciseCreate(BaseModel):
    name: str
    notes: str | None

    _check_empty_name = schema_validator("name")(check_empty_string("name"))


class ExerciseAddToWorkout(BaseModel):
    exercise_id: UUID
    workout_id: UUID

    _check_ids = schema_validator("exercise_id", "workout_id")(check_is_uuid)


class ExerciseUpdate(BaseModel):
    exercise_id: UUID
    name: str | None
    notes: str | None

    _check_ids = schema_validator("exercise_id")(check_is_uuid)
    _check_empty_name = schema_validator("name")(check_empty_string("name"))


class ExerciseDelete(BaseModel):
    exercise_id: UUID

    _check_ids = schema_validator("exercise_id")(check_is_uuid)
