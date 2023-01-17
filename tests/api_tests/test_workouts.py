import json
from typing import Any
from uuid import uuid4

import pytest

from swole_v2.errors.messages import (
    FIELD_CANNOT_BE_EMPTY,
    INCORRECT_DATE_FORMAT,
    INVALID_ID,
    NAME_AND_DATE_MUST_BE_UNIQUE,
    NO_WORKOUT_FOUND,
)
from swole_v2.models import Workout
from swole_v2.schemas import ErrorResponse, SuccessResponse

from .base import APITestBase, fake


# fmt: off
class TestWorkouts(APITestBase):
    invalid_workout_id_params = (
        "workout_id, message",
        [
            pytest.param(uuid4(), NO_WORKOUT_FOUND, id="Test random id fails."),
            pytest.param(fake.random_digit(), INVALID_ID, id="Test non uuid id fails.")
        ],
    )

    async def test_workout_get_all(self) -> None:
        workouts = await self.sample.workouts()
        response = SuccessResponse(**(await self.client.post("/workouts/all")).json())

        assert response.results
        assert response.code == "ok"
        assert len(response.results) == len(workouts)

    async def test_workout_detail_succeeds(self) -> None:
        workout = await self.sample.workout()

        response = SuccessResponse(
            **(await self.client.post("/workouts/detail", json={"workout_id": str(workout.id)})).json()
        )

        assert response.results
        assert response.code == "ok"
        assert response.results == [
            {"name": workout.name, "date": workout.date.strftime("%Y-%m-%d")}
        ]

    @pytest.mark.parametrize(*invalid_workout_id_params)
    async def test_workout_detail_fails_with_invalid_workout_id(self, workout_id: Any, message: str) -> None:
        response = ErrorResponse(**(await self.client.post("/workouts/detail", json={"workout_id": str(workout_id)})).json())

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
    async def test_workout_create(self, name: str, date: str, should_succeed: bool, error_message: str | None) -> None:
        data = {"name": name, "date": date}
        response = await self.client.post("/workouts/create", json=data)

        if should_succeed:
            success_response = SuccessResponse(**response.json())

            assert success_response.code == "ok"
            assert success_response.results
            assert success_response.results == [data]
        else:
            error_response = ErrorResponse(**response.json())

            assert error_response.code == "error"
            assert error_response.message == error_message

    async def test_workout_create_succeeds_when_creating_workout_with_same_name_and_date_as_workout_owned_by_different_user(self) -> None:
        name = fake.text()
        date = fake.date()
        await self.sample.workout(user=await self.sample.user(), name=name, date=date)

        response = SuccessResponse(**(await self.client.post("/workouts/create", json={"name": name, "date": date})).json())

        assert response.results
        assert response.code == "ok"
        assert response.results == [{"name": name, "date": date}]

    async def test_workout_create_fails_with_unique_constraint(self) -> None:
        # Add first workout
        name = fake.text()
        date = fake.date()
        await self.sample.workout(name=name, date=date)

        # Create second workout with same name and date
        response = ErrorResponse(**(await self.client.post("/workouts/create", json={"name": name, "date": date})).json())

        assert response.code == "error"
        assert response.message == NAME_AND_DATE_MUST_BE_UNIQUE

    async def test_workout_delete_with_valid_id(self) -> None:
        workout = await self.sample.workout()

        result = SuccessResponse(
            **(await self.client.post("/workouts/delete", json={"workout_id": str(workout.id)})).json()
        )
        deleted_exercise = json.loads(await self.db.query_single_json(
            "SELECT Workout FILTER .id = <uuid>$workout_id", workout_id=workout.id
        ))

        assert deleted_exercise is None
        assert result.code == "ok"
        assert result.results is None

    async def test_workout_delete_with_invalid_workout_id(self) -> None:
        result = ErrorResponse(
            **(await self.client.post("/workouts/delete", json={"workout_id": str(fake.random_digit())})).json()
        )

        assert result.code == "error"
        assert result.message == INVALID_ID

    @pytest.mark.parametrize(
        "name, date",
        [
            pytest.param(fake.text(), fake.date(), id="Test update name and date succeeds"),
            pytest.param(None, fake.date(), id="Test update only date succeeds"),
            pytest.param(fake.text(), None, id="Test update only name succeeds"),
        ],
    )
    async def test_workout_update_succeeds(self, name: str | None, date: str | None) -> None:
        workout = await self.sample.workout()
        data = {"workout_id": str(workout.id), "name": name, "date": date}
        original_workout_date = workout.date.strftime("%Y-%m-%d")
        original_workout_name = workout.name

        response = SuccessResponse(**(await self.client.post("/workouts/update", json=data)).json())

        updated_workout = Workout.parse_raw(await self.db.query_single_json(
            "SELECT Workout {name, date} FILTER .id = <uuid>$workout_id", workout_id=workout.id
        ))

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
    async def test_workout_update_fails_with_params(self, name: str, date: str, message: str) -> None:
        workout = await self.sample.workout()
        data = {"workout_id": str(workout.id), "name": name, "date": date}

        response = ErrorResponse(**(await self.client.post("/workouts/update", json=data)).json())
        not_updated_workout = Workout.parse_raw(await self.db.query_single_json(
            "SELECT Workout {name, date} FILTER .id = <uuid>$workout_id", workout_id=workout.id
        ))

        assert response.code == "error"
        assert response.message == message
        assert not_updated_workout.name == workout.name
        assert not_updated_workout.date == workout.date

    async def test_workout_update_fails_when_updating_to_existing_name_and_date(self) -> None:
        workout_one = await self.sample.workout()
        workout_two = await self.sample.workout()
        data = {
            "workout_id": str(workout_two.id),
            "name": workout_one.name,
            "date": workout_one.date.strftime("%Y-%m-%d"),
        }

        response = ErrorResponse(**(await self.client.post("/workouts/update", json=data)).json())

        assert response.code == "error"
        assert response.message == NAME_AND_DATE_MUST_BE_UNIQUE

    async def test_workout_update_fails_with_invalid_workout_id(self) -> None:
        data = {
            "workout_id": str(fake.random_digit()),
            "name": fake.name(),
            "date": fake.date()
        }

        response = ErrorResponse(**(await self.client.post("/workouts/update", json=data)).json())

        assert response.code == "error"
        assert response.message == INVALID_ID
# fmt: on
