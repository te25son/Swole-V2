from faker import Faker
from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session

from swole_v2.app import SwoleApp
from swole_v2.models import User
from swole_v2.security import get_current_active_user

fake = Faker()


class APITestBase:
    @pytest.fixture(autouse=True)
    def common_fixtures(
        self,
        test_app: SwoleApp,
        test_user: User,
        test_client: TestClient,
        test_session: Session,
    ) -> None:
        self.user = test_user
        self.client = test_client
        self.session = test_session
        self.app = test_app

        self.override_active_user(self.user)

    def override_active_user(self, user: User) -> None:
        self.app.app.dependency_overrides[get_current_active_user] = lambda: user
