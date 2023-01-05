import datetime as dt
from uuid import UUID

from sqlmodel import SQLModel

from .validators import (
    check_date_format,
    check_empty_string,
    check_is_uuid,
    schema_validator,
)


class WorkoutDetail(SQLModel):
    workout_id: UUID

    _check_id = schema_validator("workout_id")(check_is_uuid)


class WorkoutCreate(SQLModel):
    name: str
    date: dt.date

    _check_empty_name = schema_validator("name")(check_empty_string("name"))
    _check_date_format = schema_validator("date")(check_date_format())


class WorkoutUpdate(SQLModel):
    workout_id: UUID
    name: str | None = None
    date: dt.date | None = None

    _check_id = schema_validator("workout_id")(check_is_uuid)
    _check_empty_name = schema_validator("name")(check_empty_string("name", allow_none=True))
    _check_date_format = schema_validator("date")(check_date_format(allow_none=True))


class WorkoutDelete(SQLModel):
    workout_id: UUID

    _check_id = schema_validator("workout_id")(check_is_uuid)
