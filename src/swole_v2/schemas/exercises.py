from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from .validators import check_empty_string, check_is_uuid, schema_validator


class ExerciseDetail(BaseModel):
    exercise_id: UUID

    _check_id = schema_validator("exercise_id")(check_is_uuid)


class ExerciseCreate(BaseModel):
    name: str
    notes: str | None = None

    _check_empty_name = schema_validator("name")(check_empty_string("name"))


class ExerciseUpdate(BaseModel):
    exercise_id: UUID
    name: str | None = None
    notes: str | None = None

    _check_ids = schema_validator("exercise_id")(check_is_uuid)
    _check_empty_name = schema_validator("name")(check_empty_string("name", allow_none=True))


class ExerciseDelete(BaseModel):
    exercise_id: UUID

    _check_ids = schema_validator("exercise_id")(check_is_uuid)


class ExerciseProgress(BaseModel):
    exercise_id: UUID

    _check_ids = schema_validator("exercise_id")(check_is_uuid)
