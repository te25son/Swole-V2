from edgedb import Client as EdgeDB
from edgedb import create_client
from fastapi.testclient import TestClient
import pytest

from swole_v2.app import SwoleApp
from swole_v2.models import User
from swole_v2.settings import get_settings

from .factories import Sample


@pytest.fixture(scope="session")
def test_app() -> SwoleApp:
    return SwoleApp()


@pytest.fixture(scope="session")
def test_client(test_app: SwoleApp) -> TestClient:
    return TestClient(test_app.app)


@pytest.fixture(scope="session", autouse=True)
def test_database() -> EdgeDB:
    return create_client(dsn=get_settings().EDGEDB_DSN)


@pytest.fixture(scope="function")
def test_user() -> User:
    return Sample().user()


@pytest.fixture(scope="function")
def test_sample(test_user: User) -> Sample:
    return Sample(test_user)
