from fastapi.testclient import TestClient
import pytest
from sqlalchemy.future import Engine
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from swole_v2.app import SwoleApp
from swole_v2.models import User
from swole_v2.settings import get_settings

from .factories import UserFactory


@pytest.fixture(scope="session")
def test_app() -> SwoleApp:
    return SwoleApp()


@pytest.fixture(scope="session")
def test_client(test_app: SwoleApp) -> TestClient:
    return TestClient(test_app.app)


@pytest.fixture(scope="session", autouse=True)
def test_database() -> Engine:
    engine = create_engine(
        url=get_settings().DB_CONNECTION,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=True,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def test_session(test_database: Engine) -> Session:  # type: ignore
    with Session(test_database) as session:
        yield session


@pytest.fixture(scope="function")
def test_user() -> User:
    return UserFactory.create_sync()
