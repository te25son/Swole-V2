from typing import Any
from uuid import uuid4

import pytest

from swole_v2.database.repositories.exercises import NO_EXERCISE_FOUND
from swole_v2.database.repositories.workouts import NO_WORKOUT_FOUND
from swole_v2.database.validators import INVALID_ID
from swole_v2.models import ErrorResponse, ExerciseRead, SuccessResponse

from ..factories import ExerciseFactory, UserFactory, WorkoutFactory
from .base import APITestBase, fake


class TestExercises(APITestBase):
    def test_exercise_get_all_succeeds(self) -> None:
        exercises = ExerciseFactory.create_batch_sync(user=self.user, size=5)

        response = SuccessResponse(**self.client.post("/exercises/all").json())

        assert response.results
        assert response.code == "ok"
        assert len(response.results) == len(exercises)
        assert all(result in response.results for result in [ExerciseRead(**e.dict()).dict() for e in exercises])

    def test_exercise_get_all_fails_with_invalid_user_id(self) -> None:
        WorkoutFactory.create_sync(user=UserFactory.create_sync(), exercises=ExerciseFactory.create_batch_sync(size=5))

        response = ErrorResponse(**self.client.post("/exercises/all").json())

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

    def test_exercise_detail_succeeds(self) -> None:
        exercise = ExerciseFactory.create_sync(workouts=WorkoutFactory.create_batch_sync(user=self.user, size=5))

        response = SuccessResponse(
            **self.client.post("/exercises/detail", json={"exercise_id": str(exercise.id)}).json()
        )

        assert response.results
        assert response.code == "ok"
        assert response.results == [ExerciseRead(**exercise.dict()).dict()]

    def test_exercise_detail_fails_with_invalid_user_id(self) -> None:
        exercise = ExerciseFactory.create_sync(
            workouts=WorkoutFactory.create_batch_sync(user=UserFactory.create_sync(), size=5)
        )

        response = ErrorResponse(**self.client.post("/exercises/detail", json={"exercise_id": str(exercise.id)}).json())

        assert response.code == "error"
        assert response.message == NO_EXERCISE_FOUND

    @pytest.mark.parametrize(
        "exercise_id, message",
        [
            pytest.param(uuid4(), NO_EXERCISE_FOUND, id="Test random uuid fails"),
            pytest.param(fake.random_digit(), INVALID_ID, id="Test random digit fails"),
            pytest.param(
                ExerciseFactory.create_sync(
                    workouts=WorkoutFactory.create_batch_sync(user=UserFactory.create_sync(), size=1)
                ).id,
                NO_EXERCISE_FOUND,
                id="Test other owned exercise id fails",
            ),
        ],
    )
    def test_exercise_detail_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        WorkoutFactory.create_sync(user=self.user, exercises=ExerciseFactory.create_batch_sync(size=5))

        response = ErrorResponse(**self.client.post("/exercises/detail", json={"exercise_id": str(exercise_id)}).json())

        assert response.code == "error"
        assert response.message == message

    def test_exercise_create_succeeds(self) -> None:
        workout = WorkoutFactory.create_sync(user=self.user)
        data = {"workout_id": str(workout.id), "name": fake.text()}

        response = SuccessResponse(**self.client.post("/exercises/add", json=data).json())

        assert response.results
        assert response.code == "ok"
        assert response.results == [ExerciseRead(**data).dict()]
