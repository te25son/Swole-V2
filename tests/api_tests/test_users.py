from __future__ import annotations

import json
from typing import Any

import pytest

from swole_v2.dependencies.passwords import hash_password
from swole_v2.errors.messages import INCORRECT_USERNAME_OR_PASSWORD
from swole_v2.models import Token, UserRead
from swole_v2.schemas import ErrorResponse, SuccessResponse

from .base import APITestBase, fake


class TestUsers(APITestBase):
    async def test_login_succeeds(self) -> None:
        password = fake.word()
        user = await self.sample.user(hashed_password=await hash_password(password))
        response = await self.client.post("/api/v2/auth/token", json={"username": user.username, "password": password})
        token = Token(**response.json())

        assert token.token_type == "bearer"
        # assert token.access_token == await create_access_token(data=dict(username=user.username))

    async def test_login_with_invalid_creds_fails(self) -> None:
        password = fake.word()
        user = await self.sample.user(hashed_password=await hash_password(fake.word()))
        response = await self._post_error("auth/token", data={"username": user.username, "password": password})

        assert response.message == INCORRECT_USERNAME_OR_PASSWORD

    async def test_login_with_nonexisting_user_fails(self) -> None:
        response = await self._post_error("auth/token", data={"username": fake.word(), "password": fake.word()})

        assert response.message == INCORRECT_USERNAME_OR_PASSWORD

    @pytest.mark.parametrize(
        "data, message",
        [
            pytest.param({"password": fake.word()}, "Field Required (username).", id="Missing username fails"),
            pytest.param({"username": fake.word()}, "Field Required (password).", id="Missing password fails"),
            pytest.param({}, "Field Required (username).", id="Empty json fails"),
        ],
    )
    async def test_login_with_missing_json_fields_fails(self, data: dict[str, Any], message: str) -> None:
        response = await self._post_error("auth/token", data=data)

        assert response.message == message

    async def test_user_profile_succeeds(self) -> None:
        response = await self._post_success("users/profile")

        assert response.results
        assert response.results == [json.loads(UserRead(**response.results[0]).json())]

    async def _post_success(self, endpoint: str, data: dict[str, Any] | None = None) -> SuccessResponse:
        response = SuccessResponse(**(await self.client.post(f"/api/v2/{endpoint}", json=data or {})).json())
        assert response.code == "ok"
        return response

    async def _post_error(self, endpoint: str, data: dict[str, Any] | None = None) -> ErrorResponse:
        response = ErrorResponse(**(await self.client.post(f"/api/v2/{endpoint}", json=data or {})).json())
        assert response.code == "error"
        return response
