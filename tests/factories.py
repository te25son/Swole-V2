from random import choice
from typing import Any, TypeVar

from pydantic_factories import (
    Ignore,
    ModelFactory,
    SyncPersistenceProtocol,
    Use,
)
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from swole_v2.models import Exercise, Set, User, Workout, WorkoutExerciseLink
from swole_v2.settings import get_settings

T = TypeVar("T", bound=SQLModel)


# ============ PERSISTENCE HANDLERS =============


class SqlModelSyncPersistenceHandler(SyncPersistenceProtocol[T]):
    def __init__(self) -> None:
        # copied from engine creation in conftest
        self.database = create_engine(
            url=get_settings().DB_CONNECTION,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=True,
        )

    def save(self, data: T) -> T:
        with Session(self.database, expire_on_commit=False) as session:
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


class UserFactory(BaseFactory[User]):
    __model__ = User


class ExerciseFactory(BaseFactory[Exercise]):
    __model__ = Exercise


class WorkoutFactory(BaseFactory[Workout]):
    __model__ = Workout


class WorkoutExerciseLinkFactory(BaseFactory[WorkoutExerciseLink]):
    __model__ = WorkoutExerciseLink


class SetFactory(BaseFactory[Set]):
    __model__ = Set

    rep_count = Use(choice, [*range(1, 501)])
    weight = Use(choice, [*range(1, 10001)])


# =================== SAMPLE ===================


class Sample:
    def __init__(self, user: User | None = None):
        self.test_user = user or self.user()

    def user(self, **kwargs: Any) -> User:
        return UserFactory.create_sync(**kwargs)

    def users(self, size: int = 5, **kwargs: Any) -> list[User]:
        return UserFactory.create_batch_sync(size=size, **kwargs)

    def workout(self, user: User | None = None, **kwargs: Any) -> Workout:
        return WorkoutFactory.create_sync(user=user or self.test_user, **kwargs)

    def workouts(self, user: User | None = None, size: int = 5, **kwargs: Any) -> list[Workout]:
        return WorkoutFactory.create_batch_sync(size=size, user=user or self.test_user, **kwargs)

    def exercise(self, user: User | None = None, **kwargs: Any) -> Exercise:
        return ExerciseFactory.create_sync(user=user or self.test_user, **kwargs)

    def exercises(self, user: User | None = None, size: int = 5, **kwargs: Any) -> list[Exercise]:
        return ExerciseFactory.create_batch_sync(size=size, user=user or self.test_user, **kwargs)

    def workout_exercise_link(self, user: User | None = None, **kwargs: Any) -> WorkoutExerciseLink:
        return WorkoutExerciseLinkFactory.create_sync(
            workout=self.workout(user or self.test_user), exercise=self.exercise(user or self.test_user), **kwargs
        )

    def new_workout_exercise_link(
        self, workout: Workout | None = None, exercise: Exercise | None = None, **kwargs: Any
    ) -> WorkoutExerciseLink:
        return WorkoutExerciseLinkFactory.create_sync(
            workout=workout or self.workout(), exercise=exercise or self.exercise(), **kwargs
        )

    def set(self, link: WorkoutExerciseLink | None = None, **kwargs: Any) -> Set:
        return SetFactory.create_sync(workout_exercise_link=link or self.workout_exercise_link(), **kwargs)

    def sets(self, link: WorkoutExerciseLink | None = None, size: int = 5, **kwargs: Any) -> list[Set]:
        return SetFactory.create_batch_sync(
            size=size, workout_exercise_link=link or self.workout_exercise_link(), **kwargs
        )
