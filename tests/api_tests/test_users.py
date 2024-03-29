from __future__ import annotations

import json
from typing import Any

import pytest

from swole_v2.dependencies.passwords import hash_password
from swole_v2.errors.messages import INCORRECT_USERNAME_OR_PASSWORD, USER_ALREADY_EXISTS
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
            pytest.param(
                {"password": fake.word()}, "Field Required. Hint: (body > username).", id="Missing username fails"
            ),
            pytest.param(
                {"username": fake.word()}, "Field Required. Hint: (body > password).", id="Missing password fails"
            ),
            pytest.param({}, "Field Required. Hint: (body > username).", id="Empty json fails"),
        ],
    )
    async def test_login_with_missing_json_fields_fails(self, data: dict[str, Any], message: str) -> None:
        response = await self._post_error("auth/token", data=data)

        assert response.message == message

    async def test_user_profile_succeeds(self) -> None:
        response = await self._post_success("users/profile")

        assert response.results
        assert response.results == [json.loads(UserRead(**response.results[0]).model_dump_json())]

    async def test_user_create_succeeds(self) -> None:
        data = [{"username": (username := fake.uuid4()), "password": fake.uuid4(), "email": (email := fake.email())}]
        response = await self._post_success("users/create", data)

        assert response.results
        assert "id" in response.results[0]
        assert ("username", username) in response.results[0].items()
        assert ("email", email) in response.results[0].items()
        assert ("disabled", False) in response.results[0].items()

    async def test_user_create_fails_with_username_that_already_exists(self) -> None:
        data = [
            {
                "username": self.user.username,
                "password": fake.uuid4(),
            }
        ]
        response = await self._post_error("users/create", data)

        assert response.message == USER_ALREADY_EXISTS

    async def test_user_create_multiple_succeeds(self) -> None:
        username_1, email_1 = fake.uuid4(), fake.email()
        username_2, email_2 = fake.uuid4(), fake.email()
        data = [
            {"username": username_1, "password": fake.word(), "email": email_1},
            {"username": username_2, "password": fake.word(), "email": email_2},
        ]
        response = await self._post_success("users/create", data)
        results = response.results

        assert results
        assert len(results) == len(data)
        assert all("id" in result for result in results)
        assert any(("username", username_1) in result.items() for result in results)
        assert any(("username", username_2) in result.items() for result in results)
        assert any(("email", email_1) in result.items() for result in results)
        assert any(("email", email_2) in result.items() for result in results)

    async def test_user_create_fails_when_adding_multiple_users_with_same_username(self) -> None:
        username = fake.uuid4()
        data = [
            {"username": username, "password": fake.word()},
            {"username": username, "password": fake.word()},
        ]
        response = await self._post_error("users/create", data)

        assert response.message == USER_ALREADY_EXISTS

    async def _post_success(
        self, endpoint: str, data: dict[str, Any] | list[dict[str, Any]] | None = None
    ) -> SuccessResponse:
        response = SuccessResponse(**(await self.client.post(f"/api/v2/{endpoint}", json=data or {})).json())
        assert response.code == "ok"
        return response

    async def _post_error(
        self, endpoint: str, data: dict[str, Any] | list[dict[str, Any]] | None = None
    ) -> ErrorResponse:
        response = ErrorResponse(**(await self.client.post(f"/api/v2/{endpoint}", json=data or {})).json())
        assert response.code == "error"
        return response
