from uuid import UUID

from pydantic import BaseModel, Field, validator

from ..errors.exceptions import BusinessError
from ..errors.messages import MUST_BE_A_NON_NEGATIVE_NUMBER, MUST_BE_A_VALID_NON_NEGATIVE_NUMBER
from .validators import check_is_less_than, check_is_uuid, schema_validator


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
    # The code below is repeated in the validators.py file. It is only here so that rep_count
    # and weight are validated a second time after the validation above.
    @validator("rep_count", "weight", pre=True, always=True)
    def check_non_negative(cls, value: int) -> int:
        try:
            value_as_int = int(value)
            if value_as_int > 0:
                return value_as_int
            raise BusinessError(MUST_BE_A_NON_NEGATIVE_NUMBER)
        except (TypeError, ValueError) as exc:
            raise BusinessError(MUST_BE_A_VALID_NON_NEGATIVE_NUMBER) from exc


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
    # The code below is repeated in the validators.py file. It is only here so that rep_count
    # and weight are validated a second time after the validation above.
    @validator("rep_count", "weight", pre=True, always=True)
    def check_non_negative(cls, value: int | None) -> int | None:
        if value is None:
            return value
        else:
            if isinstance(value, int) and value > 0:
                return value
        raise BusinessError(MUST_BE_A_NON_NEGATIVE_NUMBER)
