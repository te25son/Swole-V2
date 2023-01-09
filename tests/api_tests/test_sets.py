from typing import Any
from uuid import uuid4

import pytest
from sqlmodel import select

from swole_v2.errors.messages import (
    INVALID_ID,
    NO_EXERCISE_FOUND,
    NO_SET_FOUND,
    NO_WORKOUT_FOUND,
)
from swole_v2.models import Exercise, Set, SetRead, Workout
from swole_v2.schemas import ErrorResponse, SuccessResponse

from ..factories import (
    ExerciseFactory,
    SetFactory,
    UserFactory,
    WorkoutFactory,
)
from .base import APITestBase, fake


class TestSets(APITestBase):
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

    def test_set_add_succeeds(self) -> None:
        rep_count = fake.random_digit()
        weight = fake.random_digit()
        workout = WorkoutFactory.create_sync(user=self.user)
        exercise = ExerciseFactory.create_sync(user=self.user)
        data = {
            "workout_id": str(workout.id),
            "exercise_id": str(exercise.id),
            "rep_count": rep_count,
            "weight": weight,
        }

        response = SuccessResponse(**self.client.post("/sets/add", json=data).json())

        assert response.results
        assert response.code == "ok"
        assert response.results == [{"rep_count": rep_count, "weight": weight}]

    def test_set_add_fails_with_exercise_belonging_to_other_user(self) -> None:
        rep_count = fake.random_digit()
        weight = fake.random_digit()
        workout = WorkoutFactory.create_sync(user=self.user)
        exercise = ExerciseFactory.create_sync(user=UserFactory.create_sync())
        data = {
            "workout_id": str(workout.id),
            "exercise_id": str(exercise.id),
            "rep_count": rep_count,
            "weight": weight,
        }

        response = ErrorResponse(**self.client.post("/sets/add", json=data).json())

        assert response.code == "error"
        assert response.message == NO_EXERCISE_FOUND

    def test_set_add_fails_with_workout_belonging_to_other_user(self) -> None:
        rep_count = fake.random_digit()
        weight = fake.random_digit()
        workout = WorkoutFactory.create_sync(user=UserFactory.create_sync())
        exercise = ExerciseFactory.create_sync(user=self.user)
        data = {
            "workout_id": str(workout.id),
            "exercise_id": str(exercise.id),
            "rep_count": rep_count,
            "weight": weight,
        }

        response = ErrorResponse(**self.client.post("/sets/add", json=data).json())

        assert response.code == "error"
        assert response.message == NO_WORKOUT_FOUND

    @pytest.mark.parametrize(
        "workout_id, exercise_id, message",
        [
            pytest.param(uuid4(), uuid4(), NO_EXERCISE_FOUND, id="Test random uuid fails."),
            pytest.param(fake.random_digit(), fake.random_digit(), INVALID_ID, id="Test non uuid fails."),
            pytest.param(
                WorkoutFactory.create_sync(user=(user := UserFactory.create_sync())).id,
                ExerciseFactory.create_sync(user=user).id,  # type: ignore
                NO_EXERCISE_FOUND,
                id="Test workout and exercise belonging to other user fails.",
            ),
        ],
    )
    def test_set_fails_with_invalid_ids(self, workout_id: Any, exercise_id: Any, message: str) -> None:
        rep_count = fake.random_digit()
        weight = fake.random_digit()
        data = {
            "workout_id": str(workout_id),
            "exercise_id": str(exercise_id),
            "rep_count": rep_count,
            "weight": weight,
        }

        response = ErrorResponse(**self.client.post("/sets/add", json=data).json())

        assert response.code == "error"
        assert response.message == message

    def test_set_delete_succeeds(self) -> None:
        workout = WorkoutFactory.create_sync(user=self.user)
        exercise = ExerciseFactory.create_sync(user=self.user)
        set = SetFactory.create_sync(workout=workout, exercise=exercise)
        data = {
            "set_id": str(set.id),
            "workout_id": str(workout.id),
            "exercise_id": str(exercise.id),
        }

        response = SuccessResponse(**self.client.post("/sets/delete", json=data).json())

        post_workout = self.session.exec(select(Workout).where(Workout.id == workout.id)).one()
        post_exercise = self.session.exec(select(Exercise).where(Exercise.id == exercise.id)).one()
        post_set = self.session.exec(select(Set).where(Set.id == set.id)).one_or_none()

        assert set not in post_workout.sets
        assert set not in post_exercise.sets
        assert post_set is None
        assert response.code == "ok"
        assert response.results == None

    @pytest.mark.parametrize(
        "workout_id, exercise_id, set_id, message",
        [
            pytest.param(uuid4(), uuid4(), uuid4(), NO_SET_FOUND, id="Test random uuid fails."),
            pytest.param(
                fake.random_digit(), fake.random_digit(), fake.random_digit(), INVALID_ID, id="Test non uuid fails."
            ),
            pytest.param(
                (workout := WorkoutFactory.create_sync(user=(user := UserFactory.create_sync()))).id,
                (exercise := ExerciseFactory.create_sync(user=user)).id,
                SetFactory.create_sync(workout=workout, exercise=exercise).id,  # type: ignore
                NO_SET_FOUND,
                id="Test set belonging to other user fails.",
            ),
        ],
    )
    def test_set_delete_fails(self, workout_id: Any, exercise_id: Any, set_id: Any, message: str) -> None:
        data = {
            "set_id": str(set_id),
            "workout_id": str(workout_id),
            "exercise_id": str(exercise_id),
        }

        response = ErrorResponse(**self.client.post("/sets/delete", json=data).json())

        assert response.code == "error"
        assert response.message == message

    @pytest.mark.parametrize(
        "rep_count, weight", [
            pytest.param(fake.random_digit(), None, id="Test only update rep count succeeds."),
            pytest.param(None, fake.random_digit(), id="Test only update weight succeeds."),
            pytest.param(fake.random_digit(), fake.random_digit(), id="Test update both rep count and weight succeeds."),
        ]
    )
    def test_update_succeeds(self, rep_count: int | None, weight: int | None) -> None:
        workout = WorkoutFactory.create_sync(user=self.user)
        exercise = ExerciseFactory.create_sync(user=self.user)
        set = SetFactory.create_sync(workout=workout, exercise=exercise)
        data = {
            "rep_count": rep_count,
            "weight": weight,
            "set_id": str(set.id),
            "workout_id": str(workout.id),
            "exercise_id": str(exercise.id),
        }

        response = SuccessResponse(**self.client.post("/sets/update", json=data).json())

        assert response.results
        assert response.code == "ok"
        assert response.results == [
            {"rep_count": rep_count or set.rep_count, "weight": weight or set.weight}
        ]
