from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, TypeVar

from edgedb import AsyncIOClient
from fastapi import Depends
from pydantic import BaseModel

from ..database import get_async_client

if TYPE_CHECKING:
    from uuid import UUID

T = TypeVar("T", bound=BaseModel)


class BaseRepository:
    def __init__(self, client: AsyncIOClient) -> None:
        self.client = client

    @classmethod
    async def as_dependency(cls, client: AsyncIOClient = Depends(get_async_client)) -> "BaseRepository":
        return cls(client)

    async def query_json(
        self, query: str, user_id: UUID | None, data: list[T] | None = None, unique: bool = True
    ) -> list[dict[str, Any]]:
        async for transaction in self.client.transaction():
            async with transaction:
                if data:
                    # Convert from set to list to ensure unique values
                    trusted_data = list({d.json() for d in data}) if unique else [d.json() for d in data]
                    result = await transaction.query_json(query, data=trusted_data, user_id=user_id)
                else:
                    result = await transaction.query_json(query, user_id=user_id)
        return json.loads(result)
