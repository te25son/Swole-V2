import pytest
from edgedb import AsyncIOClient
from faker import Faker
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from swole_v2.app import SwoleApp
from swole_v2.database.repositories import UserRepository
from swole_v2.dependencies.auth import get_current_active_user
from swole_v2.dependencies.settings import get_settings
from swole_v2.errors.messages import COULD_NOT_VALIDATE_CREDENTIALS, INACTIVE_USER

from ..factories import Sample

fake = Faker()


class TestAuth:
    @pytest.fixture(autouse=True)
    async def common_fixtures(self, test_sample: Sample, test_app: SwoleApp, test_database: AsyncIOClient) -> None:
        self.sample = test_sample
        self.app = test_app
        self.db = test_database
        self.repo = UserRepository(client=self.db, settings=get_settings())

    async def test_get_current_user_succeeds(self) -> None:
        user = await self.sample.user()
        token = await self.repo.create_access_token(data={"username": user.username})
        current_user = await get_current_active_user(
            authorization=HTTPAuthorizationCredentials(scheme="Bearer", credentials=token), repository=self.repo
        )
        assert user == current_user

    async def test_get_current_user_fails_with_invalid_token(self) -> None:
        user_with_token = await self.sample.user()
        token = await self.repo.create_access_token(data={"token": user_with_token.username})
        await self.assert_http_exception(token, COULD_NOT_VALIDATE_CREDENTIALS)

    async def test_get_current_user_fails_with_non_existing_user(self) -> None:
        token = await self.repo.create_access_token(data={"username": fake.word()})
        await self.assert_http_exception(token, COULD_NOT_VALIDATE_CREDENTIALS)

    async def test_get_current_user_fails_with_incorrect_secret(self) -> None:
        token = await self.repo.create_access_token(data={"username": fake.word()})
        get_settings().SECRET_KEY = fake.word()
        await self.assert_http_exception(token, COULD_NOT_VALIDATE_CREDENTIALS)

    async def test_inactive_user_fails(self) -> None:
        user = await self.sample.user(disabled=True)
        token = await self.repo.create_access_token(data={"username": user.username})
        await self.assert_http_exception(token, INACTIVE_USER)

    async def assert_http_exception(self, token: str, message: str) -> None:
        with pytest.raises(HTTPException) as error:
            await get_current_active_user(
                authorization=HTTPAuthorizationCredentials(scheme="Bearer", credentials=token), repository=self.repo
            )
        assert error.value.detail == message
