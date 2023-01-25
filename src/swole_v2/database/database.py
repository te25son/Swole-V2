from edgedb import AsyncIOClient, create_async_client

from ..dependencies.settings import get_settings


def get_async_client() -> AsyncIOClient:
    return create_async_client(dsn=get_settings().EDGEDB_DSN)
