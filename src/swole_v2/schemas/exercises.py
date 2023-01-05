from uuid import UUID

from sqlmodel import SQLModel

from .validators import check_empty_string, check_is_uuid, schema_validator


class ExerciseDetail(SQLModel):
    exercise_id: UUID

    _check_id = schema_validator("exercise_id")(check_is_uuid)


class ExerciseCreate(SQLModel):
    name: str

    _check_empty_name = schema_validator("name")(check_empty_string("name"))


class ExerciseAddToWorkout(SQLModel):
    exercise_id: UUID
    workout_id: UUID

    _check_ids = schema_validator("exercise_id", "workout_id")(check_is_uuid)


class ExerciseUpdate(SQLModel):
    exercise_id: UUID
    name: str

    _check_ids = schema_validator("exercise_id")(check_is_uuid)
    _check_empty_name = schema_validator("name")(check_empty_string("name"))


class ExerciseDelete(SQLModel):
    exercise_id: UUID

    _check_ids = schema_validator("exercise_id")(check_is_uuid)
