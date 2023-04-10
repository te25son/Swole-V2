from __future__ import annotations

import json
from typing import Any

from edgedb import AsyncIOClient
from fastapi import Depends

from ..database import get_async_client


class BaseRepository:
    def __init__(self, client: AsyncIOClient) -> None:
        self.client = client

    @classmethod
    async def as_dependency(cls, client: AsyncIOClient = Depends(get_async_client)) -> "BaseRepository":
        return cls(client)

    async def query_json(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        async for transaction in self.client.transaction():
            async with transaction:
                result = await transaction.query_json(query, *args, **kwargs)
        return json.loads(result)
