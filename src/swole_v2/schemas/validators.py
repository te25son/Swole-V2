from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Callable
from uuid import UUID

from pydantic import validator
from pydantic.typing import AnyCallable

if TYPE_CHECKING:
    from pydantic.typing import AnyClassMethod

from ..exceptions import BusinessError

FIELD_CANNOT_BE_EMPTY = "Field '{}' cannot be empty."
INCORRECT_DATE_FORMAT = "Incorrect date format, should be YYYY-MM-DD"
INVALID_ID = "Invalid ID"


def schema_validator(*fields: str, **kwargs: Any) -> Callable[[AnyCallable], "AnyClassMethod"]:
    return validator(*fields, allow_reuse=True, pre=True, always=True, **kwargs)


def check_is_uuid(id: str) -> UUID:
    try:
        return UUID(id)
    except (ValueError, AttributeError):
        raise BusinessError(INVALID_ID)


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


def check_date_format(allow_none: bool = False) -> Callable[[bool], date | None]:
    # Should always be run with pre=True so pydantic doesn't convert it first.
    def wrapper(value: Any) -> date | None:
        if allow_none and (value is None):
            return value
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            raise BusinessError(INCORRECT_DATE_FORMAT)

    return wrapper
