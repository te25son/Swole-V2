from edgedb import AsyncIOClient
from fastapi import Depends

from ..database import get_async_client


class BaseRepository:
    def __init__(self, client: AsyncIOClient) -> None:
        self.client = client

    @classmethod
    async def as_dependency(cls, client: AsyncIOClient = Depends(get_async_client)) -> "BaseRepository":
        return cls(client)
