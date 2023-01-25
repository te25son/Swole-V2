from typing import Any

from swole_v2.dependencies.passwords import hash_password
from swole_v2.errors.messages import INCORRECT_USERNAME_OR_PASSWORD
from swole_v2.models import Token, UserRead
from swole_v2.schemas import ErrorResponse, SuccessResponse

from .base import APITestBase, fake


class TestUsers(APITestBase):
    async def test_login_succeeds(self) -> None:
        password = fake.word()
        user = await self.sample.user(hashed_password=await hash_password(password))
        response = await self.client.post("/api/v2/auth/token", json=dict(username=user.username, password=password))
        token = Token(**response.json())

        assert token.token_type == "bearer"
        # assert token.access_token == await create_access_token(data=dict(username=user.username))

    async def test_login_with_invalid_creds_fails(self) -> None:
        password = fake.word()
        user = await self.sample.user(hashed_password=await hash_password(fake.word()))
        response = await self._post_error("auth/token", data=dict(username=user.username, password=password))

        assert response.message == INCORRECT_USERNAME_OR_PASSWORD

    async def test_user_profile_succeeds(self) -> None:
        response = await self._post_success("users/profile")

        assert response.results
        assert response.results == [UserRead(**response.results[0]).dict()]

    async def _post_success(self, endpoint: str, data: dict[str, Any] = {}) -> SuccessResponse:
        response = SuccessResponse(**(await self.client.post(f"/api/v2/{endpoint}", json=data)).json())
        assert response.code == "ok"
        return response

    async def _post_error(self, endpoint: str, data: dict[str, Any] = {}) -> ErrorResponse:
        response = ErrorResponse(**(await self.client.post(f"/api/v2/{endpoint}", json=data)).json())
        assert response.code == "error"
        return response
