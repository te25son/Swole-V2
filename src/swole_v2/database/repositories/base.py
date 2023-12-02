from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, TypeVar

from fastapi import Depends
from pydantic import BaseModel

from ..database import get_async_client

if TYPE_CHECKING:
    from uuid import UUID

    from edgedb import AsyncIOClient

T = TypeVar("T", bound=BaseModel)


class BaseRepository:
    def __init__(self, client: AsyncIOClient) -> None:
        self.client = client

    @classmethod
    async def as_dependency(cls, client: AsyncIOClient = Depends(get_async_client)) -> "BaseRepository":
        return cls(client)

    async def query_json(
        self, query: str, data: list[T] | None, unique: bool = True, **kwargs: Any
    ) -> list[dict[str, Any]]:
        async for transaction in self.client.transaction():
            async with transaction:
                if data:
                    # Convert from set to list to ensure unique values
                    trusted_data = (
                        list({d.model_dump_json() for d in data}) if unique else [d.model_dump_json() for d in data]
                    )
                    result = await transaction.query_json(query, data=trusted_data, **kwargs)
                else:
                    result = await transaction.query_json(query, **kwargs)
        return json.loads(result)

    async def query_owned_json(
        self, query: str, user_id: UUID | None, data: list[T] | None = None, unique: bool = True
    ) -> list[dict[str, Any]]:
        return await self.query_json(query, data, unique, user_id=user_id)
