from typing import Any
from uuid import uuid4

import pytest

from swole_v2.database.repositories.workouts import NO_WORKOUT_FOUND
from swole_v2.database.validators import INVALID_ID
from swole_v2.models import ErrorResponse, SuccessResponse

from . import APITestBase, fake
from ..factories import ExerciseFactory, UserFactory, WorkoutFactory


class TestWorkouts(APITestBase):
    def test_exercise_get_all_succeeds(self) -> None:
        workout = WorkoutFactory.create_sync(user=self.user, exercises=ExerciseFactory.create_batch_sync(size=5))

        response = SuccessResponse(**self.client.post("/exercises/all", json={"workout_id": str(workout.id)}).json())

        assert response.results
        assert response.code == "ok"
        assert len(response.results) == len(workout.exercises)

    def test_exercise_get_all_fails_with_invalid_user_id(self) -> None:
        workout = WorkoutFactory.create_sync(
            user=UserFactory.create_sync(), exercises=ExerciseFactory.create_batch_sync(size=5)
        )

        response = ErrorResponse(**self.client.post("/exercises/all", json={"workout_id": str(workout.id)}).json())

        assert response.code == "error"
        assert response.message == NO_WORKOUT_FOUND

    @pytest.mark.parametrize(
        "workout_id, message",
        [
            pytest.param(uuid4(), NO_WORKOUT_FOUND, id="Test random uuid fails"),
            pytest.param(fake.random_digit(), INVALID_ID, id="Test random digit fails"),
            pytest.param(
                WorkoutFactory.create_sync(user=UserFactory.create_sync()).id,
                NO_WORKOUT_FOUND,
                id="Test other owned workout id fails",
            ),
        ],
    )
    def test_exercise_get_all_fails_with_invalid_workout_id(self, workout_id: Any, message: str) -> None:
        WorkoutFactory.create_sync(user=self.user, exercises=ExerciseFactory.create_batch_sync(size=5))

        response = ErrorResponse(**self.client.post("/exercises/all", json={"workout_id": str(workout_id)}).json())

        assert response.code == "error"
        assert response.message == message
