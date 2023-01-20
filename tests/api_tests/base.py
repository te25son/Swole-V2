from edgedb import AsyncIOClient
from faker import Faker
from httpx import AsyncClient
import pytest

from swole_v2.app import SwoleApp
from swole_v2.models import User
from swole_v2.security import get_current_active_user

from ..factories import Sample

fake = Faker()


class APITestBase:
    @pytest.fixture(autouse=True)
    async def common_fixtures(
        self,
        test_app: SwoleApp,
        test_user: User,
        test_client: AsyncClient,
        test_database: AsyncIOClient,
        test_sample: Sample,
    ) -> None:
        self.user = test_user
        self.client = test_client
        self.db = test_database
        self.app = test_app
        self.sample = test_sample

        await self.override_active_user(self.user)

    async def override_active_user(self, user: User) -> None:
        self.app.app.dependency_overrides[get_current_active_user] = lambda: user
