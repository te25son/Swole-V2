from uuid import UUID

from pydantic import BaseModel, NonNegativeInt

from .validators import check_is_uuid, schema_validator


class SetGetAll(BaseModel):
    workout_id: UUID
    exercise_id: UUID

    _check_ids = schema_validator("workout_id", "exercise_id")(check_is_uuid)


class SetAdd(BaseModel):
    rep_count: NonNegativeInt
    weight: NonNegativeInt
    workout_id: UUID
    exercise_id: UUID

    _check_ids = schema_validator("workout_id", "exercise_id")(check_is_uuid)


class SetDelete(BaseModel):
    set_id: UUID
    workout_id: UUID
    exercise_id: UUID

    _check_ids = schema_validator("set_id", "workout_id", "exercise_id")(check_is_uuid)


class SetUpdate(BaseModel):
    rep_count: NonNegativeInt | None = None
    weight: NonNegativeInt | None = None
    set_id: UUID
    workout_id: UUID
    exercise_id: UUID

    _check_ids = schema_validator("set_id", "workout_id", "exercise_id")(check_is_uuid)
