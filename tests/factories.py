from pydantic_factories import Ignore, ModelFactory

from swole_v2 import models


class ExerciseFactory(ModelFactory[models.Exercise]):
    __model__ = models.Exercise

    id = Ignore()


class WorkoutFactory(ModelFactory[models.Workout]):
    __model__ = models.Workout

    id = Ignore()


class UserFactory(ModelFactory[models.User]):
    __model__ = models.User

    id = Ignore()
