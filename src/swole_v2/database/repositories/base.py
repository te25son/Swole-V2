from edgedb import Client
from fastapi import Depends

from ..database import get_client


class BaseRepository:
    def __init__(self, client: Client) -> None:
        self.client = client

    @classmethod
    def as_dependency(cls, client: Client = Depends(get_client)) -> "BaseRepository":
        return cls(client)
