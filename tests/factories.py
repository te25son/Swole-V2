from random import choice
from typing import Any, TypeVar

from edgedb import create_async_client, create_client
from pydantic import BaseModel
from pydantic_factories import Ignore, ModelFactory, Use

from swole_v2.models import Exercise, Set, User, Workout
from swole_v2.settings import get_settings

T = TypeVar("T", bound=BaseModel)


# ================== FACTORIES ==================


class BaseFactory(ModelFactory[T]):
    __allow_none_optionals__ = False

    id = Ignore()


class UserFactory(BaseFactory[User]):
    __model__ = User


class ExerciseFactory(BaseFactory[Exercise]):
    __model__ = Exercise


class WorkoutFactory(BaseFactory[Workout]):
    __model__ = Workout

    exercises = Ignore()


class SetFactory(BaseFactory[Set]):
    __model__ = Set

    rep_count = Use(choice, [*range(1, 501)])
    weight = Use(choice, [*range(1, 10001)])
    workout = Ignore()
    exercise = Ignore()


# =================== SAMPLE ===================


class Sample:
    def __init__(self, user: User | None = None) -> None:
        self.client = create_async_client(dsn=get_settings().EDGEDB_DSN)
        self.test_user = user or self._add_sync_user()

    # This method is a workaround since we cannot use await inside __init__
    @classmethod
    def _add_sync_user(cls) -> User:
        sync_client = create_client(dsn=get_settings().EDGEDB_DSN)
        user_factory = UserFactory.build()
        user = sync_client.query_single_json(
            """
            WITH user := (
                INSERT User {
                    username := <str>$username,
                    hashed_password := <str>$password,
                    email := <str>$email
                }
            )
            SELECT user {id, username, email}
            """,
            username=user_factory.username,
            password=user_factory.hashed_password,
            email=user_factory.email,
        )
        return User.parse_raw(user)

    async def user(self, **kwargs: Any) -> User:
        user_factory = UserFactory.build(**kwargs)
        user = await self.client.query_single_json(
            """
            WITH user := (
                INSERT User {
                    username := <str>$username,
                    hashed_password := <str>$password,
                    email := <str>$email
                }
            )
            SELECT user {id, username, email}
            """,
            username=user_factory.username,
            password=user_factory.hashed_password,
            email=user_factory.email,
        )
        return User.parse_raw(user)

    async def users(self, size: int = 5, **kwargs: Any) -> list[User]:
        return [await self.user(**kwargs) for _ in range(0, size)]

    async def workout(self, user: User | None = None, **kwargs: Any) -> Workout:
        workout_factory = WorkoutFactory.build(**kwargs)
        workout = await self.client.query_single_json(
            """
            WITH workout := (
                INSERT Workout {
                    name := <str>$name,
                    date := <cal::local_date>$date,
                    user := (SELECT User FILTER .id = <uuid>$user_id)
                }
            )
            SELECT workout {id, name, date}
            """,
            name=workout_factory.name,
            date=workout_factory.date,
            user_id=(user or self.test_user).id,
        )
        return Workout.parse_raw(workout)

    async def workouts(self, user: User | None = None, size: int = 5, **kwargs: Any) -> list[Workout]:
        return [await self.workout(user, **kwargs) for _ in range(0, size)]

    async def exercise(self, user: User | None = None, **kwargs: Any) -> Exercise:
        exercise_factory = ExerciseFactory.build(**kwargs)
        exercise = await self.client.query_single_json(
            """
            WITH exercise := (
                INSERT Exercise {
                    name := <str>$name,
                    user := (SELECT User FILTER .id = <uuid>$user_id)
                }
            )
            SELECT exercise {id, name}
            """,
            name=exercise_factory.name,
            user_id=(user or self.test_user).id,
        )
        return Exercise.parse_raw(exercise)

    async def exercises(self, user: User | None = None, size: int = 5, **kwargs: Any) -> list[Exercise]:
        return [await self.exercise(user, **kwargs) for _ in range(0, size)]

    async def set(self, workout: Workout | None = None, exercise: Exercise | None = None, **kwargs: Any) -> Set:
        set_factory = SetFactory.build(**kwargs)
        set = await self.client.query_single_json(
            """
            WITH exercise_set := (
                INSERT ExerciseSet {
                    weight := <int64>$weight,
                    rep_count := <int64>$rep_count,
                    workout := (SELECT Workout FILTER .id = <uuid>$workout_id),
                    exercise := (SELECT Exercise FILTER .id = <uuid>$exercise_id),
                }
            )
            SELECT exercise_set {
                id,
                weight,
                rep_count,
                exercise: {id, name},
                workout: {id, name, date}
            }
            """,
            weight=set_factory.weight,
            rep_count=set_factory.rep_count,
            workout_id=(workout or await self.workout()).id,
            exercise_id=(exercise or await self.exercise()).id,
        )
        return Set.parse_raw(set)

    async def sets(
        self, workout: Workout | None = None, exercise: Exercise | None = None, size: int = 5, **kwargs: Any
    ) -> list[Set]:
        return [await self.set(workout=workout, exercise=exercise, **kwargs) for _ in range(0, size)]
