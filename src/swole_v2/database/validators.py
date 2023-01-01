from datetime import date, datetime
from typing import Any, Callable

FIELD_CANNOT_BE_EMPTY = "Field '{}' cannot be empty."
INCORRECT_DATE_FORMAT = "Incorrect date format, should be YYYY-MM-DD"


def check_empty_string(field_name: str) -> Callable[[str], str]:
    def wrapper(value: str) -> str:
        if value.strip() == "":
            raise ValueError(FIELD_CANNOT_BE_EMPTY.format(field_name))
        return value

    return wrapper


def check_date_format(value: Any) -> date:
    # Should always be run with pre=True so pydantic doesn't convert it first.
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(INCORRECT_DATE_FORMAT)
