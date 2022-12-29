from fastapi import Depends
from sqlalchemy.future import Engine

from ..database import get_engine


class BaseRepository:
    def __init__(self, database: Engine) -> None:
        self.database = database

    @classmethod
    def as_dependency(cls, database: Engine = Depends(get_engine)) -> "BaseRepository":
        return cls(database)
