from typing import TypeVar
from random import choice

from pydantic_factories import Ignore, ModelFactory, SyncPersistenceProtocol, Use
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from swole_v2 import models
from swole_v2.settings import get_settings

T = TypeVar("T", bound=SQLModel)


# ============ PERSISTENCE HANDLERS =============


class SqlModelSyncPersistenceHandler(SyncPersistenceProtocol[T]):
    def __init__(self) -> None:
        self.database = create_engine(
            url=get_settings().DB_CONNECTION,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=True,
        )

    def save(self, data: T) -> T:
        with Session(self.database, expire_on_commit=False) as session:
            session.expire_on_commit = False
            session.add(data)
            session.commit()

            return data

    def save_many(self, data: list[T]) -> list[T]:
        with Session(self.database, expire_on_commit=False) as session:
            session.add_all(data)
            session.commit()

            return data


# ================== FACTORIES ==================


class BaseFactory(ModelFactory[T]):
    __sync_persistence__ = SqlModelSyncPersistenceHandler  # type: ignore

    id = Ignore()


class UserFactory(BaseFactory[models.User]):
    __model__ = models.User


class ExerciseFactory(BaseFactory[models.Exercise]):
    __model__ = models.Exercise


class WorkoutFactory(BaseFactory[models.Workout]):
    __model__ = models.Workout


class SetFactory(BaseFactory[models.Set]):
    __model__ = models.Set

    rep_count = Use(choice, [*range(1, 501)])
    weight = Use(choice, [*range(1, 10001)])
