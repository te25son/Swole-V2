from __future__ import annotations

import datetime
from uuid import UUID

from pydantic import BaseModel

from .validators import check_date_format, check_empty_string, check_is_uuid, schema_validator


class WorkoutDetail(BaseModel):
    workout_id: UUID

    _check_id = schema_validator("workout_id")(check_is_uuid)


class WorkoutCreate(BaseModel):
    name: str
    date: datetime.date

    _check_empty_name = schema_validator("name")(check_empty_string("name"))
    _check_date_format = schema_validator("date")(check_date_format())


class WorkoutUpdate(BaseModel):
    workout_id: UUID
    name: str | None = None
    date: datetime.date | None = None

    _check_id = schema_validator("workout_id")(check_is_uuid)
    _check_empty_name = schema_validator("name")(check_empty_string("name", allow_none=True))
    _check_date_format = schema_validator("date")(check_date_format(allow_none=True))


class WorkoutDelete(BaseModel):
    workout_id: UUID

    _check_id = schema_validator("workout_id")(check_is_uuid)


class WorkoutAddExercise(BaseModel):
    workout_id: UUID
    exercise_id: UUID

    _check_id = schema_validator("workout_id", "exercise_id")(check_is_uuid)


class WorkoutGetAllExercises(BaseModel):
    workout_id: UUID

    _check_id = schema_validator("workout_id")(check_is_uuid)


class WorkoutCopy(BaseModel):
    workout_id: UUID
    date: datetime.date

    _check_id = schema_validator("workout_id")(check_is_uuid)
    _check_date_format = schema_validator("date")(check_date_format())
