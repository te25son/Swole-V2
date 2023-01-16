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
        user = self.client.query_single_json(
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

    def users(self, size: int = 5, **kwargs: Any) -> list[User]:
        return [self.user(**kwargs) for _ in range(0, size)]

    def workout(self, user: User | None = None, **kwargs: Any) -> Workout:
        workout_factory = WorkoutFactory.build(**kwargs)
        workout = self.client.query_single_json(
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

    def workouts(self, user: User | None = None, size: int = 5, **kwargs: Any) -> list[Workout]:
        return [self.workout(user, **kwargs) for _ in range(0, size)]

    def exercise(self, user: User | None = None, **kwargs: Any) -> Exercise:
        exercise_factory = ExerciseFactory.build(**kwargs)
        exercise = self.client.query_single_json(
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

    def exercises(self, user: User | None = None, size: int = 5, **kwargs: Any) -> list[Exercise]:
        return [self.exercise(user, **kwargs) for _ in range(0, size)]

    def set(self, workout: Workout | None = None, exercise: Exercise | None = None, **kwargs: Any) -> Set:
        set_factory = SetFactory.build(**kwargs)
        set = self.client.query_single_json(
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
            workout_id=(workout or self.workout()).id,
            exercise_id=(exercise or self.exercise()).id,
        )
        return Set.parse_raw(set)

    def sets(
        self, workout: Workout | None = None, exercise: Exercise | None = None, size: int = 5, **kwargs: Any
    ) -> list[Set]:
        return [self.set(workout=workout, exercise=exercise, **kwargs) for _ in range(0, size)]
