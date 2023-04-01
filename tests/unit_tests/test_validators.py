from __future__ import annotations

from uuid import UUID

import pytest
from hypothesis import given
from hypothesis import strategies as st

from swole_v2.errors.exceptions import BusinessError
from swole_v2.errors.messages import (
    FIELD_CANNOT_BE_EMPTY,
    INCORRECT_DATE_FORMAT,
    INVALID_ID,
    MUST_BE_A_VALID_NON_NEGATIVE_NUMBER,
)
from swole_v2.schemas.validators import check_date_format, check_empty_string, check_is_non_negative, check_is_uuid


@given(value=st.uuids())
def test_check_valid_uuid(value: UUID) -> None:
    check_is_uuid(str(value))


@given(value=st.text())
def test_check_invalid_uuid(value: str) -> None:
    with pytest.raises(BusinessError) as ex:
        check_is_uuid(value)
    assert str(ex.value) == INVALID_ID


@given(value=st.text())
def test_check_date_format(value: str) -> None:
    with pytest.raises(BusinessError) as ex:
        check_date_format(allow_none=False)(value)  # type: ignore
    assert str(ex.value) == INCORRECT_DATE_FORMAT


def test_check_empty_string_raises_error_when_none() -> None:
    with pytest.raises(BusinessError) as ex:
        check_empty_string(field_name="name", allow_none=False)(None)  # type: ignore
    assert str(ex.value) == FIELD_CANNOT_BE_EMPTY.format("name")


def test_non_negative_fails() -> None:
    with pytest.raises(BusinessError) as ex:
        check_is_non_negative(allow_none=True)("not a negative number")  # type: ignore
    assert str(ex.value) == MUST_BE_A_VALID_NON_NEGATIVE_NUMBER
