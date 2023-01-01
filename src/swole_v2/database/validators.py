from typing import Callable

FIELD_CANNOT_BE_EMPTY = "Field '{}' cannot be empty."


def check_empty_string(field_name: str) -> Callable[[str], str]:
    def wrapper(value: str) -> str:
        if value.strip() == "":
            raise ValueError(FIELD_CANNOT_BE_EMPTY.format(field_name))
        return value

    return wrapper
