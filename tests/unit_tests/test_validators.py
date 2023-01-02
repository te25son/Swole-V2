from uuid import UUID

from hypothesis import given
from hypothesis import strategies as st
import pytest

from swole_v2.database.validators import (
    INCORRECT_DATE_FORMAT,
    INVALID_ID,
    check_date_format,
    check_is_uuid,
)
from swole_v2.exceptions import BusinessError


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
