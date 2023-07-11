from __future__ import annotations

import json
from random import choice
from typing import Any, TypeVar

from edgedb import create_async_client
from polyfactory import Ignore, Use
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

from swole_v2.dependencies.settings import get_settings
from swole_v2.models import Exercise, Set, User, Workout

T = TypeVar("T", bound=BaseModel)


# ================== FACTORIES ==================


class BaseFactory(ModelFactory[T]):
    __is_base_factory__ = True
    __allow_none_optionals__ = False

    id = Ignore()


class UserFactory(BaseFactory[User]):
    __model__ = User

    disabled = False


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
    def __init__(self) -> None:
        self.client = create_async_client(dsn=get_settings().EDGEDB_INSTANCE)

    # Needed to create instance with async user method
    async def initialize(self, user: User | None = None) -> "Sample":
        self.test_user = user or await self.user()
        return self

    async def user(self, **kwargs: Any) -> User:
        user_factory = UserFactory.build(**kwargs)
        user = await self.client.query_single_json(
            """
            WITH user := (
                INSERT User {
                    username := <str>$username,
                    hashed_password := <str>$password,
                    email := <str>$email,
                    disabled := <bool>$disabled
                }
            )
            SELECT user {id, username, hashed_password, email, disabled}
            """,
            username=user_factory.username,
            password=user_factory.hashed_password,
            email=user_factory.email,
            disabled=user_factory.disabled,
        )
        return User.model_validate_json(user)

    async def users(self, size: int = 5, **kwargs: Any) -> list[User]:
        user_factories = UserFactory.batch(size, **kwargs)
        users = await self.client.query_json(
            """
            WITH users := (
                FOR user IN array_unpack(<array<json>>$factories) UNION (
                    INSERT User {
                        username := <str>user['username'],
                        hashed_password := <str>user['hashed_password'],
                        email := <str>user['email'],
                        disabled := <bool>user['disabled']
                    }
                )
            )
            SELECT users {id, username, hashed_password, email, disabled}
            """,
            factories=[u.model_dump_json() for u in user_factories],
        )
        return [User(**u) for u in json.loads(users)]

    async def workout(
        self, user: User | None = None, exercises: list[Exercise] | None = None, **kwargs: Any
    ) -> Workout:
        workout_factory = WorkoutFactory.build(**kwargs)
        workout = await self.client.query_single_json(
            """
            WITH
                exercises := (
                    FOR id IN array_unpack(<array<uuid>>$exercise_ids) UNION (
                        SELECT Exercise FILTER .id = <uuid>id
                    )
                ),
                workout := (
                    INSERT Workout {
                        name := <str>$name,
                        date := <cal::local_date>$date,
                        user := (SELECT User FILTER .id = <uuid>$user_id),
                        exercises := assert_distinct(exercises)
                    }
                )
            SELECT workout {id, name, date, exercises: {id, name, notes}}
            """,
            name=workout_factory.name,
            date=workout_factory.date,
            user_id=(user or self.test_user).id,
            exercise_ids=[e.id for e in exercises or []],
        )
        return Workout.model_validate_json(workout)

    async def workouts(self, user: User | None = None, size: int = 5, **kwargs: Any) -> list[Workout]:
        workout_factories = WorkoutFactory.batch(size, **kwargs)
        workouts = await self.client.query_json(
            """
            WITH workouts := (
                FOR workout IN array_unpack(<array<json>>$factories) UNION (
                    INSERT Workout {
                        name := <str>workout['name'],
                        date := <cal::local_date>workout['date'],
                        user := (SELECT User FILTER .id = <uuid>$user_id)
                    }
                )
            )
            SELECT workouts {id, name, date}
            """,
            factories=[w.model_dump_json() for w in workout_factories],
            user_id=(user or self.test_user).id,
        )
        return [Workout(**w) for w in json.loads(workouts)]

    async def exercise(self, user: User | None = None, **kwargs: Any) -> Exercise:
        exercise_factory = ExerciseFactory.build(**kwargs)
        exercise = await self.client.query_single_json(
            """
            WITH exercise := (
                INSERT Exercise {
                    name := <str>$name,
                    notes := <str>$notes,
                    user := (SELECT User FILTER .id = <uuid>$user_id)
                }
            )
            SELECT exercise {id, name, notes}
            """,
            name=exercise_factory.name,
            notes=exercise_factory.notes,
            user_id=(user or self.test_user).id,
        )
        return Exercise.model_validate_json(exercise)

    async def exercises(self, user: User | None = None, size: int = 5, **kwargs: Any) -> list[Exercise]:
        exercise_factories = ExerciseFactory.batch(size, **kwargs)
        exercises = await self.client.query_json(
            """
            WITH exercises := (
                FOR exercise IN array_unpack(<array<json>>$factories) UNION (
                    INSERT Exercise {
                        name := <str>exercise['name'],
                        notes := <str>exercise['notes'],
                        user := (SELECT User FILTER .id = <uuid>$user_id)
                    }
                )
            )
            SELECT exercises {id, name, notes}
            """,
            factories=[e.model_dump_json() for e in exercise_factories],
            user_id=(user or self.test_user).id,
        )
        return [Exercise(**e) for e in json.loads(exercises)]

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
        return Set.model_validate_json(set)

    async def sets(
        self, workout: Workout | None = None, exercise: Exercise | None = None, size: int = 5, **kwargs: Any
    ) -> list[Set]:
        set_factories = SetFactory.batch(size, **kwargs)
        sets = await self.client.query_json(
            """
            WITH exercise_sets := (
                FOR exercise_set IN array_unpack(<array<json>>$factories) UNION (
                    INSERT ExerciseSet {
                        weight := <int64>exercise_set['weight'],
                        rep_count := <int64>exercise_set['rep_count'],
                        workout := (SELECT Workout FILTER .id = <uuid>$workout_id),
                        exercise := (SELECT Exercise FILTER .id = <uuid>$exercise_id),
                    }
                )
            )
            SELECT exercise_sets {
                id,
                weight,
                rep_count,
                exercise: {id, name},
                workout: {id, name, date}
            }
            """,
            factories=[s.model_dump_json() for s in set_factories],
            workout_id=(workout or await self.workout()).id,
            exercise_id=(exercise or await self.exercise()).id,
        )
        return [Set(**s) for s in json.loads(sets)]
