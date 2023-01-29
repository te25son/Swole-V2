from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Callable
from uuid import UUID

from pydantic import validator
from pydantic.typing import AnyCallable

if TYPE_CHECKING:
    from pydantic.typing import AnyClassMethod

from ..errors.exceptions import BusinessError
from ..errors.messages import (
    FIELD_CANNOT_BE_EMPTY,
    INCORRECT_DATE_FORMAT,
    INVALID_ID,
    MUST_BE_A_NON_NEGATIVE_NUMBER,
    MUST_BE_A_VALID_NON_NEGATIVE_NUMBER,
    MUST_BE_LESS_THAN,
)


def schema_validator(*fields: str, **kwargs: Any) -> Callable[[AnyCallable], "AnyClassMethod"]:
    return validator(*fields, allow_reuse=True, pre=True, always=True, **kwargs)


def check_is_uuid(id: str) -> UUID:
    try:
        return UUID(id)
    except (ValueError, AttributeError) as exc:
        raise BusinessError(INVALID_ID) from exc


def check_empty_string(field_name: str, allow_none: bool = False) -> Callable[[str], str | None]:
    def wrapper(value: Any) -> str | None:
        error = BusinessError(FIELD_CANNOT_BE_EMPTY.format(field_name))
        if allow_none and value is None:
            return value
        else:
            if value is None:
                raise error
            if isinstance(value, str) and value.strip() == "":
                raise error
        return value

    return wrapper


def check_is_non_negative(allow_none: bool = False) -> Callable[[int], int | None]:  # noqa[C901]
    def wrapper(value: Any) -> int | None:
        if allow_none and value is None:
            return value
        else:
            try:
                value_as_int = int(value)
                if value_as_int > 0:
                    return value_as_int
                raise BusinessError(MUST_BE_A_NON_NEGATIVE_NUMBER)
            except (TypeError, ValueError) as exc:
                raise BusinessError(MUST_BE_A_VALID_NON_NEGATIVE_NUMBER) from exc

    return wrapper


def check_is_less_than(number: int, allow_none: bool = False) -> Callable[[int], int | None]:  # noqa[C901]
    def wrapper(value: Any) -> int | None:
        if allow_none and value is None:
            return value
        else:
            try:
                value_as_int = int(value)
                if value_as_int < number:
                    return value_as_int
                raise BusinessError(MUST_BE_LESS_THAN.format(number))
            except (TypeError, ValueError) as exc:
                raise BusinessError(MUST_BE_A_VALID_NON_NEGATIVE_NUMBER) from exc

    return wrapper


def check_date_format(allow_none: bool = False) -> Callable[[bool], date | None]:
    # Should always be run with pre=True so pydantic doesn't convert it first.
    def wrapper(value: Any) -> date | None:
        if allow_none and (value is None):
            return value
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (ValueError, TypeError) as exc:
            raise BusinessError(INCORRECT_DATE_FORMAT) from exc

    return wrapper
