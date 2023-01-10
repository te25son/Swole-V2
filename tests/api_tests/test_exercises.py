from typing import Any
from uuid import uuid4

import pytest
from sqlmodel import select

from swole_v2.errors.messages import (
    EXERCISE_ALREADY_EXISTS_IN_WORKOUT,
    EXERCISE_WITH_NAME_ALREADY_EXISTS,
    FIELD_CANNOT_BE_EMPTY,
    INVALID_ID,
    NO_EXERCISE_FOUND,
    NO_WORKOUT_OR_EXERCISE_FOUND,
)
from swole_v2.models import Exercise, ExerciseRead, WorkoutExerciseLink
from swole_v2.schemas import ErrorResponse, SuccessResponse

from .base import APITestBase, fake, sample


class TestExercises(APITestBase):
    invalid_exercise_id_params = (
        "exercise_id, message",
        [
            pytest.param(uuid4(), NO_EXERCISE_FOUND, id="Test random id fails."),
            pytest.param(fake.random_digit(), INVALID_ID, id="Test non uuid id fails."),
            pytest.param(
                sample.workout_exercise_link().exercise_id,
                NO_EXERCISE_FOUND,
                id="Test exercise id belonging to other user fails.",
            ),
        ],
    )

    invalid_name_params = (
        "name, message",
        [
            pytest.param("", FIELD_CANNOT_BE_EMPTY.format("name"), id="Test empty name fails."),
            pytest.param("   ", FIELD_CANNOT_BE_EMPTY.format("name"), id="Test blank name fails."),
            pytest.param(None, FIELD_CANNOT_BE_EMPTY.format("name"), id="Test none name fails."),
        ],
    )

    def test_exercise_get_all_succeeds(self) -> None:
        exercises = self.sample.exercises()

        response = SuccessResponse(**self.client.post("/exercises/all").json())

        assert response.results
        assert response.code == "ok"
        assert len(response.results) == len(exercises)
        assert all(result in response.results for result in [ExerciseRead(**e.dict()).dict() for e in exercises])

    def test_exercise_get_all_returns_only_exercises_owned_by_logged_in_user(self) -> None:
        self.sample.exercises(user=self.sample.user())

        response = SuccessResponse(**self.client.post("/exercises/all").json())

        assert response.code == "ok"
        assert response.results == []

    def test_exercise_detail_succeeds(self) -> None:
        exercise = self.sample.workout_exercise_link().exercise

        response = SuccessResponse(
            **self.client.post("/exercises/detail", json={"exercise_id": str(exercise.id)}).json()
        )

        assert response.results
        assert response.code == "ok"
        assert response.results == [ExerciseRead(**exercise.dict()).dict()]

    @pytest.mark.parametrize(*invalid_exercise_id_params)
    def test_exercise_detail_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        self.sample.workout_exercise_link()

        response = ErrorResponse(**self.client.post("/exercises/detail", json={"exercise_id": str(exercise_id)}).json())

        assert response.code == "error"
        assert response.message == message

    def test_exercise_create_succeeds(self) -> None:
        name = fake.text()
        data = {"name": name}
        # Excercise with name exists but belongs to other user
        self.sample.exercise(user=self.sample.user(), name=name)

        response = SuccessResponse(**self.client.post("/exercises/create", json=data).json())

        assert response.results
        assert response.code == "ok"
        assert response.results == [ExerciseRead(**data).dict()]

    @pytest.mark.parametrize(*invalid_name_params)
    def test_exercise_create_with_invalid_name_fails(self, name: Any, message: str) -> None:
        response = ErrorResponse(**self.client.post("/exercises/create", json={"name": name}).json())

        assert response.code == "error"
        assert response.message == message

    def test_exercise_create_with_existing_name_fails(self) -> None:
        exercise = self.sample.exercise()

        response = ErrorResponse(**self.client.post("/exercises/create", json={"name": exercise.name}).json())

        assert response.code == "error"
        assert response.message == EXERCISE_WITH_NAME_ALREADY_EXISTS

    def test_exercise_add_succeeds(self) -> None:
        workout = self.sample.workout()
        exercise = self.sample.exercise()
        data = {"workout_id": str(workout.id), "exercise_id": str(exercise.id)}

        response = SuccessResponse(**self.client.post("/exercises/add", json=data).json())

        # Check link was created
        self.session.exec(
            select(WorkoutExerciseLink)
            .where(WorkoutExerciseLink.workout_id == workout.id)
            .where(WorkoutExerciseLink.exercise_id == exercise.id)
        ).one()

        assert response.results
        assert response.code == "ok"
        assert response.results == [ExerciseRead(**exercise.dict()).dict()]

    @pytest.mark.parametrize(
        "workout_id, message",
        [
            pytest.param(uuid4(), NO_WORKOUT_OR_EXERCISE_FOUND, id="Test random uuid fails."),
            pytest.param(fake.random_digit(), INVALID_ID, id="Test random digit fails."),
            pytest.param(
                sample.workout().id,
                NO_WORKOUT_OR_EXERCISE_FOUND,
                id="Test adding exercise to workout belonging to other user fails.",
            ),
        ],
    )
    def test_exercise_add_fails_with_invalid_workout_id(self, workout_id: Any, message: str) -> None:
        # Ensure the user has workouts but none matching the given id
        self.sample.workouts()
        exercise = self.sample.exercise()
        data = {"workout_id": str(workout_id), "exercise_id": str(exercise.id)}

        response = ErrorResponse(**self.client.post("/exercises/add", json=data).json())

        assert response.code == "error"
        assert response.message == message

    @pytest.mark.parametrize(
        "exercise_id, message",
        [
            pytest.param(uuid4(), NO_WORKOUT_OR_EXERCISE_FOUND, id="Test random uuid fails."),
            pytest.param(fake.random_digit(), INVALID_ID, id="Test random digit fails."),
            pytest.param(
                sample.exercise().id,
                NO_WORKOUT_OR_EXERCISE_FOUND,
                id="Test adding exercise belonging to other user to workout fails.",
            ),
        ],
    )
    def test_exercise_add_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        # Ensure the user has exercises but none matching the given id
        self.sample.exercises()
        workout = self.sample.workout()
        data = {"workout_id": str(workout.id), "exercise_id": str(exercise_id)}

        response = ErrorResponse(**self.client.post("/exercises/add", json=data).json())

        assert response.code == "error"
        assert response.message == message

    def test_exercise_add_fails_when_adding_exercise_that_already_exists_in_workout(self) -> None:
        link = self.sample.workout_exercise_link()
        data = {"workout_id": str(link.workout_id), "exercise_id": str(link.exercise_id)}

        response = ErrorResponse(**self.client.post("/exercises/add", json=data).json())

        assert response.code == "error"
        assert response.message == EXERCISE_ALREADY_EXISTS_IN_WORKOUT

    def test_exercise_update_succeeds(self) -> None:
        new_name = fake.text()
        # Existing exercise with the new name but different user should work
        self.sample.exercise(user=self.sample.user(), name=new_name)
        exercise = self.sample.exercise()

        response = SuccessResponse(
            **self.client.post("/exercises/update", json={"exercise_id": str(exercise.id), "name": new_name}).json()
        )
        updated_exercise = self.session.exec(select(Exercise).where(Exercise.id == exercise.id)).one()

        assert response.results
        assert response.code == "ok"
        assert response.results == [ExerciseRead(**updated_exercise.dict()).dict()]

    @pytest.mark.parametrize(*invalid_name_params)
    def test_exercise_update_fails_with_invalid_name(self, name: Any, message: str) -> None:
        exercise = self.sample.exercise()

        response = ErrorResponse(
            **self.client.post("/exercises/update", json={"exercise_id": str(exercise.id), "name": name}).json()
        )

        assert response.code == "error"
        assert response.message == message

    def test_exercise_update_fails_with_existing_name_and_same_user(self) -> None:
        name = self.sample.exercise().name
        exercise = self.sample.exercise()

        response = ErrorResponse(
            **self.client.post("/exercises/update", json={"exercise_id": str(exercise.id), "name": name}).json()
        )

        assert response.code == "error"
        assert response.message == EXERCISE_WITH_NAME_ALREADY_EXISTS

    @pytest.mark.parametrize(*invalid_exercise_id_params)
    def test_exercise_update_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        response = ErrorResponse(
            **self.client.post("/exercises/update", json={"exercise_id": str(exercise_id), "name": fake.text()}).json()
        )

        assert response.code == "error"
        assert response.message == message

    def test_exercise_delete_succeeds(self) -> None:
        exercise = self.sample.exercise()

        response = SuccessResponse(
            **self.client.post("exercises/delete", json={"exercise_id": str(exercise.id)}).json()
        )
        deleted_exercise = self.session.exec(select(Exercise).where(Exercise.id == exercise.id)).one_or_none()

        assert deleted_exercise is None
        assert response.code == "ok"
        assert response.results is None

    @pytest.mark.parametrize(*invalid_exercise_id_params)
    def test_exercise_delete_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        response = ErrorResponse(**self.client.post("/exercises/delete", json={"exercise_id": str(exercise_id)}).json())

        assert response.code == "error"
        assert response.message == message
