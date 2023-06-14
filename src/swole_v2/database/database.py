from __future__ import annotations

from typing import TYPE_CHECKING

from edgedb import create_async_client

from ..dependencies.settings import get_settings

if TYPE_CHECKING:
    from edgedb import AsyncIOClient


def get_async_client() -> AsyncIOClient:
    return create_async_client(dsn=get_settings().EDGEDB_INSTANCE)
