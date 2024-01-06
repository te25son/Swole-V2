from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from hypothesis import given
from hypothesis import strategies as st

from swole_v2.errors.exceptions import BusinessError
from swole_v2.errors.messages import (
    INCORRECT_DATE_FORMAT,
    INVALID_ID,
)
from swole_v2.schemas.validators import check_date_format, check_uuid

if TYPE_CHECKING:
    from uuid import UUID


@given(value=st.uuids())
def test_check_valid_uuid(value: UUID) -> None:
    check_uuid(str(value))


@given(value=st.text())
def test_check_invalid_uuid(value: str) -> None:
    with pytest.raises(BusinessError) as ex:
        check_uuid(value)
    assert str(ex.value) == INVALID_ID


@given(value=st.text())
def test_check_date_format(value: str) -> None:
    with pytest.raises(BusinessError) as ex:
        check_date_format(value)  # type: ignore
    assert str(ex.value) == INCORRECT_DATE_FORMAT
