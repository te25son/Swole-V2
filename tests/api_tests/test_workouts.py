from typing import Any
from uuid import uuid4

import pytest
from sqlmodel import select

from swole_v2.errors.messages import (
    FIELD_CANNOT_BE_EMPTY,
    INCORRECT_DATE_FORMAT,
    INVALID_ID,
    NAME_AND_DATE_MUST_BE_UNIQUE,
    NO_WORKOUT_FOUND,
)
from swole_v2.models import ExerciseRead, Workout
from swole_v2.schemas import ErrorResponse, SuccessResponse

from .base import APITestBase, fake, sample


# fmt: off
class TestWorkouts(APITestBase):
    invalid_workout_id_params = (
        "workout_id, message",
        [
            pytest.param(uuid4(), NO_WORKOUT_FOUND, id="Test random id fails."),
            pytest.param(fake.random_digit(), INVALID_ID, id="Test non uuid id fails."),
            pytest.param(
                sample.workout(exercises=sample.exercises()).id,
                NO_WORKOUT_FOUND,
                id="Test workout id belonging to other user fails.",
            ),
        ],
    )

    def test_workout_get_all(self) -> None:
        workouts = self.sample.workouts()
        response = SuccessResponse(**self.client.post("/workouts/all").json())

        assert response.results
        assert response.code == "ok"
        assert len(response.results) == len(workouts)

    def test_workout_detail_succeeds(self) -> None:
        workout = self.sample.workout()

        response = SuccessResponse(
            **self.client.post("/workouts/detail", json={"workout_id": str(workout.id)}).json()
        )

        assert response.results
        assert response.code == "ok"
        assert response.results == [
            {"name": workout.name, "date": workout.date.strftime("%Y-%m-%d")}
        ]

    @pytest.mark.parametrize(*invalid_workout_id_params)
    def test_workout_detail_fails_with_invalid_workout_id(self, workout_id: Any, message: str) -> None:
        response = ErrorResponse( **self.client.post("/workouts/detail", json={"workout_id": str(workout_id)}).json())

        assert response.code == "error"
        assert response.message == message

    @pytest.mark.parametrize(
        "name, date, should_succeed, error_message",
        [
            pytest.param("", fake.date(), False, FIELD_CANNOT_BE_EMPTY.format("name"), id="Test empty string fails",),
            pytest.param("   ", fake.date(), False, FIELD_CANNOT_BE_EMPTY.format("name"), id="Test blank string fails",),
            pytest.param(fake.text(), "12345", False, INCORRECT_DATE_FORMAT, id="Test invalid date fails",),
            pytest.param(fake.text(), "2022/01/12", False, INCORRECT_DATE_FORMAT, id="Test incorrectly formatted date fails",),
            pytest.param(fake.text(), fake.date(), True, None, id="Test succeeds"),
        ],
    )
    def test_workout_create(self, name: str, date: str, should_succeed: bool, error_message: str | None) -> None:
        data = {"name": name, "date": date}
        response = self.client.post("/workouts/create", json=data)

        if should_succeed:
            success_response = SuccessResponse(**response.json())

            assert success_response.code == "ok"
            assert success_response.results
            assert success_response.results == [data]
        else:
            error_response = ErrorResponse(**response.json())

            assert error_response.code == "error"
            assert error_response.message == error_message

    def test_workout_create_succeeds_when_creating_workout_with_same_name_and_date_as_workout_owned_by_different_user(self) -> None:
        name = fake.text()
        date = fake.date()
        self.sample.workout(user=self.sample.user(), name=name, date=date)

        response = SuccessResponse(**self.client.post("/workouts/create", json={"name": name, "date": date}).json())

        assert response.results
        assert response.code == "ok"
        assert response.results == [{"name": name, "date": date}]

    def test_workout_create_fails_with_unique_constraint(self) -> None:
        # Add first workout
        name = fake.text()
        date = fake.date()
        self.sample.workout(name=name, date=date)

        # Create second workout with same name and date
        response = ErrorResponse(**self.client.post("/workouts/create", json={"name": name, "date": date}).json())

        assert response.code == "error"
        assert response.message == NAME_AND_DATE_MUST_BE_UNIQUE

    def test_workout_delete_with_valid_id(self) -> None:
        workout = self.sample.workout()

        result = SuccessResponse(
            **self.client.post("/workouts/delete", json={"workout_id": str(workout.id)}).json()
        )
        deleted_exercise = self.session.exec(select(Workout).where(Workout.id == workout.id)).one_or_none()

        assert deleted_exercise is None
        assert result.code == "ok"
        assert result.results is None

    @pytest.mark.parametrize(*invalid_workout_id_params)
    def test_workout_delete_with_invalid_workout_id(self, workout_id: Any, message: str) -> None:
        result = ErrorResponse(
            **self.client.post("/workouts/delete", json={"workout_id": str(workout_id)}).json()
        )

        assert result.code == "error"
        assert result.message == message

    @pytest.mark.parametrize(
        "name, date",
        [
            pytest.param(fake.text(), fake.date(), id="Test update name and date succeeds"),
            pytest.param(None, fake.date(), id="Test update only date succeeds"),
            pytest.param(fake.text(), None, id="Test update only name succeeds"),
        ],
    )
    def test_workout_update_succeeds(self, name: str | None, date: str | None) -> None:
        workout = self.sample.workout()
        data = {"workout_id": str(workout.id), "name": name, "date": date}
        original_workout_date = workout.date.strftime("%Y-%m-%d")
        original_workout_name = workout.name

        response = SuccessResponse(**self.client.post("/workouts/update", json=data).json())

        updated_workout = self.session.exec(select(Workout).where(Workout.id == workout.id)).one()

        assert response.results
        assert response.results == [
            {
                "name": name or original_workout_name,
                "date": date or original_workout_date,
            }
        ]
        assert updated_workout.name == data["name"] or original_workout_name
        assert updated_workout.date.strftime("%Y-%m-%d") == data["date"] or original_workout_date

    @pytest.mark.parametrize(
        "name, date, message",
        [
            pytest.param("", fake.date(), FIELD_CANNOT_BE_EMPTY.format("name"), id="Test update with empty name fails",),
            pytest.param("   ", fake.date(), FIELD_CANNOT_BE_EMPTY.format("name"), id="Test update with blank name fails",),
            pytest.param(fake.text(), fake.text(), INCORRECT_DATE_FORMAT, id="Test update with invalid date fails",),
            pytest.param(fake.text(), "1980/03/02", INCORRECT_DATE_FORMAT, id="Test update with incorrectly formatted date fails",),
        ],
    )
    def test_workout_update_fails_with_params(self, name: str, date: str, message: str) -> None:
        workout = self.sample.workout()
        data = {"workout_id": str(workout.id), "name": name, "date": date}

        response = ErrorResponse(**self.client.post("/workouts/update", json=data).json())
        not_updated_workout = self.session.exec(select(Workout).where(Workout.id == workout.id)).one()

        assert response.code == "error"
        assert response.message == message
        assert not_updated_workout.name == workout.name
        assert not_updated_workout.date == workout.date

    def test_workout_update_fails_when_updating_to_existing_name_and_date(self) -> None:
        workout_one = self.sample.workout()
        workout_two = self.sample.workout()
        data = {
            "workout_id": str(workout_two.id),
            "name": workout_one.name,
            "date": workout_one.date.strftime("%Y-%m-%d"),
        }

        response = ErrorResponse(**self.client.post("/workouts/update", json=data).json())

        assert response.code == "error"
        assert response.message == NAME_AND_DATE_MUST_BE_UNIQUE

    @pytest.mark.parametrize(*invalid_workout_id_params)
    def test_workout_update_fails_with_invalid_workout_id(self, workout_id: Any, message: str) -> None:
        data = {
            "workout_id": str(workout_id),
            "name": fake.name(),
            "date": fake.date()
        }

        response = ErrorResponse(**self.client.post("/workouts/update", json=data).json())

        assert response.code == "error"
        assert response.message == message

    def test_get_all_exercises_by_workout_succeeds(self) -> None:
        workout = self.sample.workout()
        links = [self.sample.new_workout_exercise_link(workout) for _ in range(0, 3)]

        response = SuccessResponse(
            **self.client.post("/workouts/exercises", json={"workout_id": str(workout.id)}).json()
        )

        assert response.results
        assert response.code == "ok"
        assert all(
            exercise in [ExerciseRead(**link.exercise.dict()).dict() for link in links]
            for exercise in response.results
        )
# fmt: on
