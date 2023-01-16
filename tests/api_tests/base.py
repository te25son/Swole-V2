from edgedb import Client as EdgeDB
from faker import Faker
from fastapi.testclient import TestClient
import pytest

from swole_v2.app import SwoleApp
from swole_v2.models import User
from swole_v2.security import get_current_active_user

from ..factories import Sample

fake = Faker()
sample = Sample()


class APITestBase:
    @pytest.fixture(autouse=True)
    def common_fixtures(
        self, test_app: SwoleApp, test_user: User, test_client: TestClient, test_database: EdgeDB, test_sample: Sample
    ) -> None:
        self.user = test_user
        self.client = test_client
        self.db = test_database
        self.app = test_app
        self.sample = test_sample

        self.override_active_user(self.user)

    def override_active_user(self, user: User) -> None:
        self.app.app.dependency_overrides[get_current_active_user] = lambda: user
