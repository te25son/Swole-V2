from uuid import uuid4

import pytest

from swole_v2.errors.messages import INVALID_ID, NO_SET_FOUND
from swole_v2.models import SetRead
from swole_v2.schemas import SuccessResponse

from ..factories import (
    ExerciseFactory,
    SetFactory,
    UserFactory,
    WorkoutFactory,
)
from .base import APITestBase, fake


class TestSets(APITestBase):
    invalid_workout_and_exercise_id_params = (
        "workout_id, exercise_id, message",
        [
            pytest.param(uuid4(), uuid4(), NO_SET_FOUND, id="Test random uuid fails."),
            pytest.param(fake.random_digit(), fake.random_digit(), INVALID_ID, id="Test non uuid fails."),
            pytest.param(
                WorkoutFactory.create_sync(user=(user := UserFactory.create_sync())).id,
                ExerciseFactory.create_sync(user=user).id,  # type: ignore
                NO_SET_FOUND,
                id="Test workout and exercise belonging to other user fails.",
            ),
        ],
    )

    def test_set_get_all(self) -> None:
        workout = WorkoutFactory.create_sync(user=self.user)
        exercise = ExerciseFactory.create_sync(user=self.user)
        sets = SetFactory.create_batch_sync(workout=workout, exercise=exercise, size=5)

        response = SuccessResponse(
            **self.client.post(
                "/sets/all", json={"workout_id": str(workout.id), "exercise_id": str(exercise.id)}
            ).json()
        )

        assert response.results
        assert response.code == "ok"
        assert response.results == [SetRead(**s.dict()).dict() for s in sets]

    def test_set_get_all_only_returns_sets_owned_by_logged_in_user(self) -> None:
        user = UserFactory.create_sync()
        workout = WorkoutFactory.create_sync(user=user)
        exercise = ExerciseFactory.create_sync(user=user)
        SetFactory.create_batch_sync(workout=workout, exercise=exercise, size=5)

        response = SuccessResponse(
            **self.client.post(
                "/sets/all", json={"workout_id": str(workout.id), "exercise_id": str(exercise.id)}
            ).json()
        )

        assert response.code == "ok"
        assert response.results == []
