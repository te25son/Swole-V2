from uuid import uuid4

import pytest
from sqlmodel import select

from swole_v2.database.repositories.workouts import (
    NAME_AND_DATE_MUST_BE_UNIQUE,
    NO_WORKOUT_FOUND,
)
from swole_v2.database.validators import (
    FIELD_CANNOT_BE_EMPTY,
    INCORRECT_DATE_FORMAT,
)
from swole_v2.models import ErrorResponse, SuccessResponse, Workout

from ..factories import UserFactory, WorkoutFactory
from .base import APITestBase, fake


# fmt: off
class TestWorkouts(APITestBase):
    def test_workout_get_all(self) -> None:
        workouts = WorkoutFactory.create_batch_sync(user=self.user, size=5)
        response = SuccessResponse(**self.client.post("/workouts/all").json())

        assert response.results
        assert response.code == "ok"
        assert len(response.results) == len(workouts)

    def test_workout_detail_succeeds(self) -> None:
        workout = WorkoutFactory.create_sync(user=self.user)

        response = SuccessResponse(**self.client.post(f"/workouts/detail/{workout.id}").json())

        assert response.results
        assert response.code == "ok"
        assert response.results == [
            {"name": workout.name, "date": workout.date.strftime("%Y-%m-%d")}
        ]

    def test_workout_detail_fails_with_invalid_user_id(self) -> None:
        workout = WorkoutFactory.create_sync(user=UserFactory.create_sync())

        response = ErrorResponse(**self.client.post(f"/workouts/detail/{workout.id}").json())

        assert response.code == "error"
        assert response.message == NO_WORKOUT_FOUND

    def test_workout_detail_fails_with_invalid_workout_id(self) -> None:
        response = ErrorResponse(**self.client.post(f"/workouts/detail/{uuid4()}").json())

        assert response.code == "error"
        assert response.message == NO_WORKOUT_FOUND

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
        response = self.client.post("/workouts/add", json=data)

        if should_succeed:
            success_response = SuccessResponse(**response.json())

            assert success_response.code == "ok"
            assert success_response.results
            assert success_response.results == [data]
        else:
            error_response = ErrorResponse(**response.json())

            assert error_response.code == "error"
            assert error_response.message == error_message

    def test_workout_create_succeeds_when_creating_workout_with_same_name_and_date_but_different_user(self) -> None:
        name = fake.text()
        date = fake.date()
        WorkoutFactory.create_sync(user=UserFactory.create_sync(), name=name, date=date)

        response = SuccessResponse(**self.client.post("/workouts/add", json={"name": name, "date": date}).json())

        assert response.results
        assert response.code == "ok"
        assert response.results == [{"name": name, "date": date}]

    def test_workout_create_fails_with_unique_constraint(self) -> None:
        # Add first workout
        existing_workout = WorkoutFactory.create_sync(user=self.user)
        existing_name = existing_workout.name
        existing_date = existing_workout.date.strftime("%Y-%m-%d")

        # Create second workout with same name and date
        response = ErrorResponse(**self.client.post("/workouts/add", json={"name": existing_name, "date": existing_date}).json())

        assert response.code == "error"
        assert response.message == NAME_AND_DATE_MUST_BE_UNIQUE

    def test_workout_delete_with_valid_id(self) -> None:
        workout = WorkoutFactory.create_sync(user=self.user)

        result = SuccessResponse(**self.client.post(f"/workouts/delete/{workout.id}").json())

        assert result.code == "ok"
        assert result.results is None

    def test_workout_delete_with_invalid_user_id(self) -> None:
        workout = WorkoutFactory.create_sync(user=UserFactory.create_sync())

        result = ErrorResponse(**self.client.post(f"/workouts/delete/{workout.id}").json())

        assert result.code == "error"
        assert result.message == NO_WORKOUT_FOUND

    def test_workout_delete_with_invalid_workout_id(self) -> None:
        result = ErrorResponse(**self.client.post(f"/workouts/delete/{uuid4()}").json())

        assert result.code == "error"
        assert result.message == NO_WORKOUT_FOUND

    @pytest.mark.parametrize(
        "name, date",
        [
            pytest.param(fake.text(), fake.date(), id="Test update name and date succeeds"),
            pytest.param(None, fake.date(), id="Test update only date succeeds"),
            pytest.param(fake.text(), None, id="Test update only name succeeds"),
        ],
    )
    def test_workout_update_succeeds(self, name: str | None, date: str | None) -> None:
        workout = WorkoutFactory.create_sync(user=self.user)
        update_data = {"name": name, "date": date}
        original_workout_date = workout.date.strftime("%Y-%m-%d")
        original_workout_name = workout.name

        response = SuccessResponse(**self.client.post(f"/workouts/update/{workout.id}", json=update_data).json())

        updated_workout = self.session.exec(select(Workout).where(Workout.id == workout.id)).one()

        assert response.results
        assert response.results == [
            {
                "name": name or original_workout_name,
                "date": date or original_workout_date,
            }
        ]
        assert updated_workout.name == update_data["name"] or original_workout_name
        assert updated_workout.date.strftime("%Y-%m-%d") == update_data["date"] or original_workout_date

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
        workout = WorkoutFactory.create_sync(user=self.user)
        update_data = {"name": name, "date": date}

        response = ErrorResponse(**self.client.post(f"/workouts/update/{workout.id}", json=update_data).json())
        not_updated_workout = self.session.exec(select(Workout).where(Workout.id == workout.id)).one()

        assert response.code == "error"
        assert response.message == message
        assert not_updated_workout.name == workout.name
        assert not_updated_workout.date == workout.date

    def test_workout_update_fails_when_updating_to_existing_name_and_date(self) -> None:
        workout_one = WorkoutFactory.create_sync(user=self.user)
        workout_two = WorkoutFactory.create_sync(user=self.user)
        update_data = {
            "name": workout_one.name,
            "date": workout_one.date.strftime("%Y-%m-%d"),
        }

        response = ErrorResponse(**self.client.post(f"/workouts/update/{workout_two.id}", json=update_data).json())

        assert response.code == "error"
        assert response.message == NAME_AND_DATE_MUST_BE_UNIQUE

    def test_workout_update_fails_with_invalid_user_id(self) -> None:
        workout = WorkoutFactory.create_sync(user=UserFactory.create_sync())
        update_data = {"name": fake.name(), "date": fake.date()}

        result = ErrorResponse(**self.client.post(f"/workouts/update/{workout.id}", json=update_data).json())

        assert result.code == "error"
        assert result.message == NO_WORKOUT_FOUND

    def test_workout_update_fails_with_invalid_workout_id(self) -> None:
        WorkoutFactory.create_sync(user=self.user)
        update_data = {"name": fake.name(), "date": fake.date()}

        result = ErrorResponse(**self.client.post(f"/workouts/update/{uuid4()}", json=update_data).json())

        assert result.code == "error"
        assert result.message == NO_WORKOUT_FOUND
# fmt: on
