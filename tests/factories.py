import json
from random import choice
from typing import Any, TypeVar

from edgedb import create_client
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
    def __init__(self, user: User | None = None):
        self.client = create_client(dsn=get_settings().EDGEDB_DSN)
        self.test_user = user or self.user()

    def user(self, **kwargs: Any) -> User:
        user_factory = UserFactory.build(**kwargs)
        result = json.loads(
            self.client.query_single_json(
                "INSERT User {username := <str>$username, hashed_password := <str>$password, email := <str>$email}",
                username=user_factory.username,
                password=user_factory.hashed_password,
                email=user_factory.email,
            )
        )
        user = self.client.query_single_json(
            "SELECT User {id, username, email} FILTER .id = <uuid>$user_id", user_id=result["id"]
        )
        return User.parse_raw(user)

    def users(self, size: int = 5, **kwargs: Any) -> list[User]:
        return [self.user(**kwargs) for _ in range(0, size)]

    def workout(self, user: User | None = None, **kwargs: Any) -> Workout:
        workout_factory = WorkoutFactory.build(**kwargs)
        result = json.loads(
            self.client.query_single_json(
                """
                    INSERT Workout {
                    name := <str>$name,
                    date := <cal::local_date>$date,
                    user := (SELECT User FILTER .id = <uuid>$user_id)
                }""",
                name=workout_factory.name,
                date=workout_factory.date,
                user_id=user.id if user else self.test_user.id,
            )
        )
        workout = self.client.query_single_json(
            "SELECT Workout {id, name, date} FILTER .id = <uuid>$workout_id", workout_id=result["id"]
        )
        return Workout.parse_raw(workout)

    def workouts(self, user: User | None = None, size: int = 5, **kwargs: Any) -> list[Workout]:
        return [self.workout(user, **kwargs) for _ in range(0, size)]

    def exercise(self, user: User | None = None, **kwargs: Any) -> Exercise:
        exercise_factory = ExerciseFactory.build(**kwargs)
        result = json.loads(
            self.client.query_single_json(
                """
            INSERT Exercise {
                name := <str>$name,
                user := (SELECT User FILTER .id = <uuid>$user_id)
            }""",
                name=exercise_factory.name,
                user_id=user.id if user else self.test_user.id,
            )
        )
        exercise = self.client.query_single_json(
            "SELECT Exercise {id, name} FILTER .id = <uuid>$exercise_id", exercise_id=result["id"]
        )
        return Exercise.parse_raw(exercise)

    def exercises(self, user: User | None = None, size: int = 5, **kwargs: Any) -> list[Exercise]:
        return [self.exercise(user, **kwargs) for _ in range(0, size)]

    def set(self, workout: Workout | None = None, exercise: Exercise | None = None, **kwargs: Any) -> Set:
        set_factory = SetFactory.build(**kwargs)
        result = json.loads(
            self.client.query_single_json(
                """
            INSERT ExerciseSet {
                weight := <int64>$weight,
                rep_count := <int64>$rep_count,
                workout := (SELECT Workout FILTER .id = <uuid>$workout_id),
                exercise := (SELECT Exercise FILTER .id = <uuid>$exercise_id),
            }""",
                weight=set_factory.weight,
                rep_count=set_factory.rep_count,
                workout_id=workout.id if workout else self.workout().id,
                exercise_id=exercise.id if exercise else self.exercise().id,
            )
        )
        set = self.client.query_single_json(
            """SELECT ExerciseSet {
                id,
                weight,
                rep_count,
                exercise: {id, name},
                workout: {id, name, date}
            } FILTER .id = <uuid>$set_id
            """,
            set_id=result["id"],
        )
        return Set.parse_raw(set)

    def sets(
        self, workout: Workout | None = None, exercise: Exercise | None = None, size: int = 5, **kwargs: Any
    ) -> list[Set]:
        return [self.set(workout=workout, exercise=exercise, **kwargs) for _ in range(0, size)]
