from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .validators import check_is_less_than, check_is_non_negative, check_is_uuid, schema_validator


class SetGetAll(BaseModel):
    workout_id: UUID
    exercise_id: UUID

    _check_ids = schema_validator("workout_id", "exercise_id")(check_is_uuid)


class SetAdd(BaseModel):
    rep_count: int = Field(gt=0, le=500)
    weight: int = Field(gt=0, le=10000)
    workout_id: UUID
    exercise_id: UUID

    _check_ids = schema_validator("workout_id", "exercise_id")(check_is_uuid)
    _check_rep_count_less_than = schema_validator("rep_count")(check_is_less_than(501))
    _check_weight_less_than = schema_validator("weight")(check_is_less_than(10001))

    # For some reason reusing validators like the ones above does not work when validating
    # the same field more than once.
    @field_validator("rep_count", "weight", mode="before")
    def check_non_negative(cls, value: int) -> int:
        return check_is_non_negative(allow_none=False)(value)  # type: ignore[return-value]


class SetDelete(BaseModel):
    set_id: UUID

    _check_ids = schema_validator("set_id")(check_is_uuid)


class SetUpdate(BaseModel):
    set_id: UUID
    rep_count: int | None = Field(default=None, gt=0, le=500)
    weight: int | None = Field(default=None, gt=0, le=10000)

    _check_ids = schema_validator("set_id")(check_is_uuid)
    _check_rep_count_less_than = schema_validator("rep_count")(check_is_less_than(501, allow_none=True))
    _check_weight_less_than = schema_validator("weight")(check_is_less_than(10001, allow_none=True))

    # For some reason reusing validators like the ones above does not work when validating
    # the same field more than once.
    @field_validator("rep_count", "weight", mode="before")
    def check_non_negative(cls, value: int | None) -> int | None:
        return check_is_non_negative(allow_none=True)(value)  # type: ignore[arg-type]
