from __future__ import annotations

import re
from datetime import date, datetime
from typing import Annotated, Any, Callable
from uuid import UUID

from pydantic import (
    AfterValidator,
    BeforeValidator,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)

from ..errors.exceptions import BusinessError
from ..errors.messages import (
    CANNOT_BE_GREATER_THAN,
    FIELD_CANNOT_BE_EMPTY,
    INCORRECT_DATE_FORMAT,
    INVALID_ID,
    MUST_BE_A_VALID_POSITIVE_INT,
    MUST_BE_POSITIVE,
)

MAX_WEIGHT = 10000
MAX_REP_COUNT = 500


def check_non_empty(value: str, _: ValidatorFunctionWrapHandler, info: ValidationInfo) -> str:
    pattern = re.compile(r"(.|\s)*\S(.|\s)*")
    if not pattern.match(value):
        raise BusinessError(FIELD_CANNOT_BE_EMPTY.format(info.field_name))
    return value


def check_uuid(id: str) -> UUID:
    try:
        return UUID(id)
    except (ValueError, AttributeError) as exc:
        raise BusinessError(INVALID_ID) from exc


def check_positive(value: Any, _: ValidatorFunctionWrapHandler, info: ValidationInfo) -> int:
    try:
        value_as_int = int(value)
        if value_as_int <= 0:
            raise BusinessError(MUST_BE_POSITIVE.format(info.field_name))
        return value_as_int
    except (TypeError, ValueError) as exc:
        raise BusinessError(MUST_BE_A_VALID_POSITIVE_INT) from exc


def check_max(max_value: int) -> Callable[[Any], int]:
    def inner(value: Any) -> int:
        if value > max_value:
            raise BusinessError(CANNOT_BE_GREATER_THAN.format(max_value))
        return value

    return inner


def check_date_format(value: Any) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError) as exc:
        raise BusinessError(INCORRECT_DATE_FORMAT) from exc


ID = Annotated[UUID, BeforeValidator(check_uuid)]
NonEmptyString = Annotated[str, WrapValidator(check_non_empty)]
PositiveInt = Annotated[int, WrapValidator(check_positive)]
Weight = Annotated[PositiveInt, AfterValidator(check_max(MAX_WEIGHT))]
RepCount = Annotated[PositiveInt, AfterValidator(check_max(MAX_REP_COUNT))]
Date = Annotated[date, BeforeValidator(check_date_format)]
