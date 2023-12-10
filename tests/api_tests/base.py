from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from faker import Faker

from swole_v2.dependencies.auth import get_current_active_user

if TYPE_CHECKING:
    from edgedb import AsyncIOClient
    from httpx import AsyncClient

    from swole_v2.app import SwoleApp
    from swole_v2.models import User

    from ..factories import Sample

fake = Faker()


class APITestBase:
    @pytest.fixture(autouse=True)
    async def common_fixtures(  # noqa
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
