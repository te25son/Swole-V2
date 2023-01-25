import asyncio
from asyncio import AbstractEventLoop

from edgedb import AsyncIOClient, create_async_client
from httpx import AsyncClient
import pytest
import pytest_asyncio
import uvloop

from swole_v2.app import SwoleApp
from swole_v2.dependencies.settings import get_settings
from swole_v2.models import User

from .factories import Sample


@pytest.fixture(scope="session")
async def test_app() -> SwoleApp:
    return SwoleApp()


@pytest.fixture(scope="session")
async def test_client(test_app: SwoleApp) -> AsyncClient:
    return AsyncClient(app=test_app.app, base_url="http://localhost:8000/")


@pytest.fixture(scope="session", autouse=True)
async def test_database() -> AsyncIOClient:
    return create_async_client(dsn=get_settings().EDGEDB_DSN)


@pytest.fixture(scope="function")
async def test_sample() -> Sample:
    return await Sample().initialize()


@pytest.fixture(scope="function")
async def test_user(test_sample: Sample) -> User:
    return test_sample.test_user


@pytest_asyncio.fixture(scope="session")
def event_loop() -> AbstractEventLoop:  # type: ignore
    uvloop.install()
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
