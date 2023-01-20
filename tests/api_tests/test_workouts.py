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
        response = await self._post_success("/all")

        assert response.results
        assert len(response.results) == len(workouts)

    async def test_workout_detail_succeeds(self) -> None:
        workout = await self.sample.workout()

        response = await self._post_success("/detail", data={"workout_id": str(workout.id)})

        assert response.results
        assert response.results == [
            {"name": workout.name, "date": workout.date.strftime("%Y-%m-%d")}
        ]

    @pytest.mark.parametrize(*invalid_workout_id_params)
    async def test_workout_detail_fails_with_invalid_workout_id(self, workout_id: Any, message: str) -> None:
        response = await self._post_error("/detail", data={"workout_id": str(workout_id)})

        assert response.message == message

    @pytest.mark.parametrize(
        "name, date, message",
        [
            pytest.param("", fake.date(), FIELD_CANNOT_BE_EMPTY.format("name"), id="Test empty string fails",),
            pytest.param("   ", fake.date(), FIELD_CANNOT_BE_EMPTY.format("name"), id="Test blank string fails",),
            pytest.param(fake.text(), "12345", INCORRECT_DATE_FORMAT, id="Test invalid date fails",),
            pytest.param(fake.text(), "2022/01/12", INCORRECT_DATE_FORMAT, id="Test incorrectly formatted date fails",),
        ],
    )
    async def test_workout_create_fails(self, name: str, date: str, message: str) -> None:
        response = await self._post_error("/create", data={"name": name, "date": date})

        assert response.message == message

    async def test_workout_create_succeeds(self) -> None:
        name = fake.text()
        date = fake.date()
        data = dict(name=name, date=date)
        # Should pass if other workout exists with same name and date but different user
        await self.sample.workout(name=name, date=date, user=await self.sample.user())

        response = await self._post_success("/create", data=data)

        assert response.results
        assert response.results == [data]

    async def test_workout_create_fails_with_unique_constraint(self) -> None:
        # Add first workout
        name = fake.text()
        date = fake.date()
        await self.sample.workout(name=name, date=date)

        # Create second workout with same name and date
        response = await self._post_error("/create", data={"name": name, "date": date})

        assert response.message == NAME_AND_DATE_MUST_BE_UNIQUE

    async def test_workout_delete_with_valid_id(self) -> None:
        workout = await self.sample.workout()

        result = await self._post_success("/delete", data={"workout_id": str(workout.id)})
        deleted_exercise = json.loads(await self.db.query_single_json(
            "SELECT Workout FILTER .id = <uuid>$workout_id", workout_id=workout.id
        ))

        assert deleted_exercise is None
        assert result.results is None

    async def test_workout_delete_with_invalid_workout_id(self) -> None:
        result = await self._post_error("/delete", data={"workout_id": str(fake.random_digit())})

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

        response = await self._post_success("/update", data=data)

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

        response = await self._post_error("/update", data=data)
        not_updated_workout = Workout.parse_raw(await self.db.query_single_json(
            "SELECT Workout {name, date} FILTER .id = <uuid>$workout_id", workout_id=workout.id
        ))

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

        response = await self._post_error("/update", data=data)

        assert response.message == NAME_AND_DATE_MUST_BE_UNIQUE

    async def test_workout_update_fails_with_invalid_workout_id(self) -> None:
        data = {
            "workout_id": str(fake.random_digit()),
            "name": fake.name(),
            "date": fake.date()
        }

        response = await self._post_error("/update", data=data)

        assert response.message == INVALID_ID

    async def test_add_exercise_succeeds(self) -> None:
        workout = await self.sample.workout()
        exercise = await self.sample.exercise()
        data = {
            "workout_id": str(workout.id),
            "exercise_id": str(exercise.id)
        }

        response = await self._post_success("/add-exercise", data=data)
        updated_workout = Workout.parse_raw(
            await self.db.query_single_json(
                """
                SELECT Workout {name, date, exercises: {name}}
                FILTER .id = <uuid>$workout_id
                """,
                workout_id=workout.id
            )
        )
        exercises = updated_workout.exercises

        assert response.results
        assert exercises
        assert len(exercises) == 1
        assert exercise.name in [e.name for e in exercises]

    @pytest.mark.parametrize(
        "workout_id, exercise_id, message",
        [
            pytest.param(fake.random_digit(), fake.random_digit(), INVALID_ID, id="Test non uuid fails"),
            pytest.param(uuid4(), uuid4(), NO_WORKOUT_FOUND, id="Test random uuid fails"),
        ]
    )
    async def test_add_exercise_fails_with_invalid_id(self, workout_id: Any, exercise_id: Any, message: str) -> None:
        data = {
            "workout_id": str(workout_id),
            "exercise_id": str(exercise_id)
        }
        response = await self._post_error("/add-exercise", data=data)

        assert response.message == message


    @pytest.mark.parametrize(
        "no_exercises",
        [
            pytest.param(True, id="Test get all exercises returns empty list when workout has no exercises"),
            pytest.param(False, id="Test get all exercises returns all exercises belonging to workout"),
        ]
    )
    async def test_get_all_exercises_succeeds(self, no_exercises: bool) -> None:
        exercises = await self.sample.exercises(size=10)
        # add half of the exercises since the result should only return those owned by the workout
        workout = await self.sample.workout(exercises=[] if no_exercises else exercises[:5])

        response = await self._post_success("/exercises", data={"workout_id": str(workout.id)})

        if no_exercises:
            assert response.results == []
        assert response.results == [{"name": e.name, "notes": e.notes} for e in workout.exercises]  # type: ignore

    @pytest.mark.parametrize(*invalid_workout_id_params)
    async def test_get_all_exercises_fails(self, workout_id: Any, message: str) -> None:
        response = await self._post_error("/exercises", data={"workout_id": str(workout_id)})

        assert response.code == "error"
        assert response.message == message

    async def _post_success(self, endpoint: str, data: dict[str, Any] = {}) -> SuccessResponse:
        response = SuccessResponse(**(await self.client.post(f"/api/v2/workouts{endpoint}", json=data)).json())
        assert response.code == "ok"
        return response

    async def _post_error(self, endpoint: str, data: dict[str, Any]) -> ErrorResponse:
        response = ErrorResponse(**(await self.client.post(f"/api/v2/workouts{endpoint}", json=data)).json())
        assert response.code == "error"
        return response
# fmt: on
