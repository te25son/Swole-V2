from uuid import uuid4

from swole_v2.database.repositories.workouts import NO_WORKOUT_FOUND
from swole_v2.models import ErrorResponse, SuccessResponse

from . import APITestBase
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

    def test_exercise_get_all_fails_with_invalid_workout_id(self) -> None:
        WorkoutFactory.create_sync(user=self.user, exercises=ExerciseFactory.create_batch_sync(size=5))

        response = ErrorResponse(**self.client.post("/exercises/all", json={"workout_id": str(uuid4())}).json())

        assert response.code == "error"
        assert response.message == NO_WORKOUT_FOUND
