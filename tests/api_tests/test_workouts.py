from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest

from swole_v2.errors.messages import (
    FIELD_CANNOT_BE_EMPTY,
    IDS_MUST_BE_UNIQUE,
    INCORRECT_DATE_FORMAT,
    INVALID_ID,
    NAME_AND_DATE_MUST_BE_UNIQUE,
    NO_EXERCISE_FOUND,
    NO_WORKOUT_FOUND,
)
from swole_v2.models import Workout
from swole_v2.schemas import ErrorResponse, SuccessResponse

from .base import APITestBase, fake


class TestWorkouts(APITestBase):
    invalid_workout_id_params = (
        "workout_id, message",
        [
            pytest.param(uuid4(), NO_WORKOUT_FOUND, id="Test random id fails."),
            pytest.param(fake.random_digit(), INVALID_ID, id="Test non uuid id fails."),
        ],
    )

    async def test_workout_get_all_succeeds(self) -> None:
        workouts = await self.sample.workouts()
        response = await self._post_success("/all")

        assert response.results
        assert len(response.results) == len(workouts)

    async def test_workout_detail_succeeds(self) -> None:
        workout = await self.sample.workout()

        response = await self._post_success("/detail", data=[{"workout_id": str(workout.id)}])

        assert response.results
        assert response.results == [
            {"id": str(workout.id), "name": workout.name, "date": workout.date.strftime("%Y-%m-%d")}
        ]

    async def test_workout_detail_succeeds_with_multiple_workouts(self) -> None:
        workout_1 = await self.sample.workout()
        workout_2 = await self.sample.workout()
        data = [
            {"workout_id": str(workout_1.id)},
            {"workout_id": str(workout_2.id)},
        ]

        response = await self._post_success("/detail", data=data)

        assert response.results
        assert len(response.results) == 2

    async def test_workout_detail_succeeds_with_query_parameter(self) -> None:
        workout_with_exercises = await self.sample.workout(exercises=await self.sample.exercises())
        workout_without_exercises = await self.sample.workout()
        data = [
            {"workout_id": str(workout_with_exercises.id)},
            {"workout_id": str(workout_without_exercises.id)},
        ]

        response = await self._post_success("/detail?with_exercises=true", data=data)
        expected_results = [
            {
                "id": str(workout_with_exercises.id),
                "name": workout_with_exercises.name,
                "date": workout_with_exercises.date.strftime("%Y-%m-%d"),
                "exercises": [
                    {"id": str(e.id), "name": e.name, "notes": e.notes} for e in workout_with_exercises.exercises
                ],
            },
            {
                "id": str(workout_without_exercises.id),
                "name": workout_without_exercises.name,
                "date": workout_without_exercises.date.strftime("%Y-%m-%d"),
                "exercises": [],
            },
        ]

        assert response.results
        assert all(results in response.results for results in expected_results)

    @pytest.mark.parametrize(*invalid_workout_id_params)
    async def test_workout_detail_fails_with_invalid_workout_id(self, workout_id: Any, message: str) -> None:
        valid_workout = await self.sample.workout()
        data = [
            {"workout_id": str(valid_workout.id)},
            {"workout_id": str(workout_id)},
        ]

        response = await self._post_error("/detail", data=data)

        assert response.message == message

    async def test_workout_detail_fails_with_at_least_one_workout_belonging_to_another_user(self) -> None:
        workout = await self.sample.workout()
        workout_belonging_to_other_user = await self.sample.workout(user=await self.sample.user())
        data = [
            {"workout_id": str(workout.id)},
            {"workout_id": str(workout_belonging_to_other_user.id)},
        ]

        response = await self._post_error("/detail", data=data)

        assert response.message == NO_WORKOUT_FOUND

    @pytest.mark.parametrize(
        "name, date, message",
        [
            pytest.param(
                "",
                fake.date(),
                FIELD_CANNOT_BE_EMPTY.format("name"),
                id="Test empty string fails",
            ),
            pytest.param(
                "   ",
                fake.date(),
                FIELD_CANNOT_BE_EMPTY.format("name"),
                id="Test blank string fails",
            ),
            pytest.param(
                fake.text(),
                "12345",
                INCORRECT_DATE_FORMAT,
                id="Test invalid date fails",
            ),
            pytest.param(
                fake.text(),
                "2022/01/12",
                INCORRECT_DATE_FORMAT,
                id="Test incorrectly formatted date fails",
            ),
        ],
    )
    async def test_workout_create_fails(self, name: str, date: str, message: str) -> None:
        response = await self._post_error("/create", data=[{"name": name, "date": date}])

        assert response.message == message

    async def test_workout_create_succeeds(self) -> None:
        name = fake.text()
        date = fake.date()
        # Should pass if other workout exists with same name and date but different user
        await self.sample.workout(name=name, date=date, user=await self.sample.user())

        response = await self._post_success("/create", data=[{"name": name, "date": date}])

        assert response.results
        assert "id" in response.results[0]
        assert ("name", name) in response.results[0].items()
        assert ("date", date) in response.results[0].items()

    async def test_create_workout_succeeds_with_empty_data(self) -> None:
        response = await self._post_success("create/", data=[])
        assert not response.results

    async def test_workout_create_multiple_succeeds(self) -> None:
        workout_1_name, workout_1_date = fake.text(), fake.date()
        workout_2_name, workout_2_date = fake.text(), fake.date()

        response = await self._post_success(
            "/create",
            data=[
                {"name": workout_1_name, "date": workout_1_date},
                {"name": workout_2_name, "date": workout_2_date},
            ],
        )

        assert response.results
        assert "id" in response.results[0]
        assert any(("name", workout_1_name) in r.items() for r in response.results)
        assert any(("date", workout_1_date) in r.items() for r in response.results)
        assert "id" in response.results[1]
        assert any(("name", workout_2_name) in r.items() for r in response.results)
        assert any(("date", workout_2_date) in r.items() for r in response.results)

    async def test_workout_create_does_not_add_others_to_database_when_one_fails(self) -> None:
        workout_1_name, workout_1_date = fake.text(), fake.date()
        workout_2_name, workout_2_date = fake.text(), fake.date()
        # Create an existing workout with the same name and date as one of the workouts
        await self.sample.workout(name=workout_2_name, date=workout_2_date)

        response = await self._post_error(
            "/create",
            data=[
                {"name": workout_1_name, "date": workout_1_date},
                {"name": workout_2_name, "date": workout_2_date},
            ],
        )

        # Assert only pre-existing workout still belongs to user
        results = json.loads(
            await self.db.query_json(
                "SELECT Workout {name, date} FILTER .user.id = <uuid>$user_id", user_id=self.user.id
            )
        )
        assert len(results) == 1
        assert ("name", workout_2_name) in results[0].items()
        assert ("date", workout_2_date) in results[0].items()
        assert response.message == NAME_AND_DATE_MUST_BE_UNIQUE

    async def test_workout_create_fails_with_unique_constraint(self) -> None:
        # Add first workout
        name = fake.text()
        date = fake.date()
        await self.sample.workout(name=name, date=date)

        # Create second workout with same name and date
        response = await self._post_error("/create", data=[{"name": name, "date": date}])

        assert response.message == NAME_AND_DATE_MUST_BE_UNIQUE

    async def test_workout_delete_with_valid_id(self) -> None:
        # Make sure that we can delete a workout that has linked exercises
        workout = await self.sample.workout(exercises=await self.sample.exercises())

        result = await self._post_success("/delete", data=[{"workout_id": str(workout.id)}])
        deleted_workout = json.loads(
            await self.db.query_single_json("SELECT Workout FILTER .id = <uuid>$workout_id", workout_id=workout.id)
        )

        assert deleted_workout is None
        assert result.results == []

    async def test_workout_delete_mulitple_succeeds(self) -> None:
        workout_1 = await self.sample.workout()
        workout_2 = await self.sample.workout()
        data = [
            {"workout_id": str(workout_1.id)},
            {"workout_id": str(workout_2.id)},
        ]

        result = await self._post_success("/delete", data=data)
        deleted_workout_1 = json.loads(
            await self.db.query_single_json("SELECT Workout FILTER .id = <uuid>$id", id=workout_1.id)
        )
        deleted_workout_2 = json.loads(
            await self.db.query_single_json("SELECT Workout FILTER .id = <uuid>$id", id=workout_2.id)
        )

        assert deleted_workout_1 is None
        assert deleted_workout_2 is None
        assert result.results == []

    async def test_workout_delete_fails_with_workout_belonging_to_other_user(self) -> None:
        workout = await self.sample.workout()
        workout_belonging_to_other_user = await self.sample.workout(user=await self.sample.user())
        data = [
            {"workout_id": str(workout.id)},
            {"workout_id": str(workout_belonging_to_other_user.id)},
        ]

        result = await self._post_error("/delete", data=data)

        assert result.message == NO_WORKOUT_FOUND

    @pytest.mark.parametrize(*invalid_workout_id_params)
    async def test_workout_delete_with_invalid_workout_id(self, workout_id: Any, message: str) -> None:
        valid_workout = await self.sample.workout()
        data = [
            {"workout_id": str(valid_workout.id)},
            {"workout_id": str(workout_id)},
        ]

        result = await self._post_error("/delete", data=data)

        assert result.message == message

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

        response = await self._post_success("/update", data=[data])

        updated_workout = Workout.parse_raw(
            await self.db.query_single_json(
                "SELECT Workout {name, date} FILTER .id = <uuid>$workout_id", workout_id=workout.id
            )
        )

        assert response.results
        assert response.results == [
            {
                "id": str(workout.id),
                "name": name or original_workout_name,
                "date": date or original_workout_date,
            }
        ]
        assert updated_workout.name == data["name"] or original_workout_name
        assert updated_workout.date.strftime("%Y-%m-%d") == data["date"] or original_workout_date

    @pytest.mark.parametrize(
        "name, date, message",
        [
            pytest.param(
                "",
                fake.date(),
                FIELD_CANNOT_BE_EMPTY.format("name"),
                id="Test update with empty name fails",
            ),
            pytest.param(
                "   ",
                fake.date(),
                FIELD_CANNOT_BE_EMPTY.format("name"),
                id="Test update with blank name fails",
            ),
            pytest.param(
                fake.text(),
                fake.text(),
                INCORRECT_DATE_FORMAT,
                id="Test update with invalid date fails",
            ),
            pytest.param(
                fake.text(),
                "1980/03/02",
                INCORRECT_DATE_FORMAT,
                id="Test update with incorrectly formatted date fails",
            ),
        ],
    )
    async def test_workout_update_fails_with_params(self, name: str, date: str, message: str) -> None:
        workout = await self.sample.workout()
        data = {"workout_id": str(workout.id), "name": name, "date": date}

        response = await self._post_error("/update", data=[data])
        not_updated_workout = Workout.parse_raw(
            await self.db.query_single_json(
                "SELECT Workout {name, date} FILTER .id = <uuid>$workout_id", workout_id=workout.id
            )
        )

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

        response = await self._post_error("/update", data=[data])

        assert response.message == NAME_AND_DATE_MUST_BE_UNIQUE

    @pytest.mark.parametrize(*invalid_workout_id_params)
    async def test_workout_update_fails_with_invalid_workout_id(self, workout_id: Any, message: str) -> None:
        data = {"workout_id": str(workout_id), "name": fake.name(), "date": fake.date()}

        response = await self._post_error("/update", data=[data])

        assert response.message == message

    async def test_workout_update_multiple_succeeds(self) -> None:
        workout_1 = await self.sample.workout()
        workout_2 = await self.sample.workout()
        workout_1_new_name, workout_1_new_date = fake.text(), fake.date()
        workout_2_new_name, workout_2_new_date = fake.text(), fake.date()
        data = [
            {"workout_id": str(workout_1.id), "name": workout_1_new_name, "date": workout_1_new_date},
            {"workout_id": str(workout_2.id), "name": workout_2_new_name, "date": workout_2_new_date},
        ]

        response = await self._post_success("/update", data=data)
        updated_workout_1 = Workout.parse_raw(
            await self.db.query_single_json(
                "SELECT Workout {id, name, date} FILTER .id = <uuid>$workout_id", workout_id=workout_1.id
            )
        )
        updated_workout_2 = Workout.parse_raw(
            await self.db.query_single_json(
                "SELECT Workout {id, name, date} FILTER .id = <uuid>$workout_id", workout_id=workout_2.id
            )
        )

        assert response.results
        assert updated_workout_1.name == workout_1_new_name
        assert updated_workout_1.date == datetime.strptime(workout_1_new_date, "%Y-%m-%d").date()
        assert updated_workout_2.name == workout_2_new_name
        assert updated_workout_2.date == datetime.strptime(workout_2_new_date, "%Y-%m-%d").date()

    async def test_workout_update_fails_when_updating_same_workout_multiple_times(self) -> None:
        workout = await self.sample.workout()
        data = [
            {"workout_id": str(workout.id), "name": fake.text()},
            {"workout_id": str(workout.id), "date": fake.date()},
        ]

        response = await self._post_error("/update", data=data)

        assert response.message == IDS_MUST_BE_UNIQUE

    async def test_workout_update_fails_when_updating_at_least_one_workout_not_belonging_to_user(self) -> None:
        workout = await self.sample.workout()
        workout_belonging_to_other_user = await self.sample.workout(user=await self.sample.user())
        data = [
            {"workout_id": str(workout.id), "name": fake.text()},
            {"workout_id": str(workout_belonging_to_other_user.id), "name": fake.text()},
        ]

        response = await self._post_error("/update", data=data)

        assert response.message == NO_WORKOUT_FOUND

    async def test_add_exercise_succeeds(self) -> None:
        workout = await self.sample.workout()
        exercise = await self.sample.exercise()
        data = {"workout_id": str(workout.id), "exercise_id": str(exercise.id)}

        response = await self._post_success("/add-exercises", data=[data])
        updated_workout = Workout.parse_raw(
            await self.db.query_single_json(
                """
                SELECT Workout {name, date, exercises: {name}}
                FILTER .id = <uuid>$workout_id
                """,
                workout_id=workout.id,
            )
        )
        exercises = updated_workout.exercises

        assert response.results
        assert exercises
        assert len(exercises) == 1
        assert exercise.name in [e.name for e in exercises]

    async def test_add_multiple_exercises_succeeds(self) -> None:
        num_of_exercise_to_add = 10
        workout = await self.sample.workout()
        exercises = await self.sample.exercises(size=num_of_exercise_to_add)
        data = [{"workout_id": str(workout.id), "exercise_id": str(exercise.id)} for exercise in exercises]

        response = await self._post_success("/add-exercises", data=data)
        updated_workout = Workout.parse_raw(
            await self.db.query_single_json(
                """
                SELECT Workout {name, date, exercises: {name}}
                FILTER .id = <uuid>$workout_id
                """,
                workout_id=workout.id,
            )
        )
        workout_exercises = updated_workout.exercises

        assert response.results
        assert workout_exercises
        assert len(workout_exercises) == num_of_exercise_to_add
        assert all(e.name in [e.name for e in workout_exercises] for e in exercises)

    async def test_add_multiple_exercises_to_multiple_workouts_succeeds(self) -> None:
        num_of_workouts_to_update = 10
        workouts = await self.sample.workouts(size=num_of_workouts_to_update)
        exercise = await self.sample.exercise()
        data = [{"workout_id": str(workout.id), "exercise_id": str(exercise.id)} for workout in workouts]

        response = await self._post_success("/add-exercises", data=data)
        query_results = json.loads(
            await self.db.query_json(
                """
                WITH workouts := (
                    FOR data IN array_unpack(<array<json>>$data) UNION (
                        SELECT Workout FILTER .id = <uuid>data['workout_id']
                    )
                )
                SELECT workouts {name, date, exercises: {name}}
                """,
                data=[json.dumps(d) for d in data],
            )
        )
        updated_workouts = [Workout(**r) for r in query_results]

        assert response.results
        assert len(response.results) == num_of_workouts_to_update
        assert all(exercise.name in [e.name for e in workout.exercises] for workout in updated_workouts)

    async def test_add_the_same_exercise_to_a_workout_mulitple_times_succeeds(self) -> None:
        workout = await self.sample.workout()
        exercise = await self.sample.exercise()
        data = [{"workout_id": str(workout.id), "exercise_id": str(exercise.id)} for _ in range(5)]

        response = await self._post_success("/add-exercises", data=data)
        updated_workout = Workout.parse_raw(
            await self.db.query_single_json(
                """
                SELECT Workout {name, date, exercises: {name}}
                FILTER .id = <uuid>$workout_id
                """,
                workout_id=workout.id,
            )
        )
        workout_exercises = updated_workout.exercises

        assert response.results
        assert len(response.results) == 1
        # Should have only added the exercise once
        assert len(workout_exercises) == 1
        assert exercise.name == workout_exercises[0].name

    async def test_add_exercise_to_non_existing_workout_returns_empty_list(self) -> None:
        exercise = await self.sample.exercise()
        data = [{"workout_id": str(uuid4()), "exercise_id": str(exercise.id)}]

        response = await self._post_success("/add-exercises", data=data)

        assert not response.results

    async def test_add_exercise_fails_with_non_existing_exercise(self) -> None:
        workout = await self.sample.workout()
        data = [{"workout_id": str(workout.id), "exercise_id": str(uuid4())}]

        response = await self._post_error("/add-exercises", data=data)

        assert response.message == NO_EXERCISE_FOUND

    async def test_add_exercise_fails_when_adding_exercise_from_other_user(self) -> None:
        workout = await self.sample.workout()
        exercise = await self.sample.exercise(user=await self.sample.user())
        data = [{"workout_id": str(workout.id), "exercise_id": str(exercise.id)}]

        response = await self._post_error("/add-exercises", data=data)

        assert response.message == NO_EXERCISE_FOUND

    async def test_add_exercise_fails_with_invalid_id(self) -> None:
        data = {"workout_id": str(fake.random_digit()), "exercise_id": str(fake.random_digit())}
        response = await self._post_error("/add-exercises", data=[data])

        assert response.message == INVALID_ID

    async def test_workout_copy_succeeds(self) -> None:
        exercises = await self.sample.exercises()
        workout = await self.sample.workout(exercises=exercises)
        date = fake.date()

        response = await self._post_success("/copy", data=[{"workout_id": str(workout.id), "date": date}])

        workout_results = json.loads(
            await self.db.query_json(
                """
                SELECT Workout {id, name, date, exercises: {id, name, notes}}
                FILTER .name = <str>$name
                """,
                name=workout.name,
            )
        )
        workouts = [Workout(**r) for r in workout_results]
        new_workout_id = [w.id for w in workouts if w.id != workout.id][0]

        assert len(workouts) == 2
        assert all(len(w.exercises) == len(exercises) for w in workouts)
        assert all(e in exercises for w in workouts for e in w.exercises)
        assert response.results == [{"id": str(new_workout_id), "name": workout.name, "date": date}]

    @pytest.mark.parametrize(*invalid_workout_id_params)
    async def test_workout_copy_fails_with_invalid_workout_ids(self, workout_id: Any, message: str) -> None:
        response = await self._post_error("/copy", data=[{"workout_id": str(workout_id), "date": fake.date()}])

        assert response.message == message

    @pytest.mark.parametrize(
        "date",
        [
            pytest.param("2022/12/15", id="Test invalid date format fails"),
            pytest.param(None, id="Test no date fails"),
        ],
    )
    async def test_workout_copy_fails_with_improperly_formatted_date(self, date: Any) -> None:
        workout = await self.sample.workout()
        response = await self._post_error("/copy", data=[{"workout_id": str(workout.id), "date": date}])

        assert response.message == INCORRECT_DATE_FORMAT

    async def test_cannot_copy_workout_belonging_to_other_user(self) -> None:
        workout = await self.sample.workout(user=await self.sample.user())
        response = await self._post_error("/copy", data=[{"workout_id": str(workout.id), "date": fake.date()}])

        assert response.message == NO_WORKOUT_FOUND

    async def test_cannot_copy_workout_using_same_name_and_date(self) -> None:
        date = fake.date()
        workout = await self.sample.workout(date=date)

        response = await self._post_error("/copy", data=[{"workout_id": str(workout.id), "date": date}])

        assert response.message == NAME_AND_DATE_MUST_BE_UNIQUE

    async def test_workout_copy_multiple_succeeds(self) -> None:
        workout_1 = await self.sample.workout(exercises=await self.sample.exercises())
        workout_2 = await self.sample.workout(exercises=await self.sample.exercises())
        copy_1_date = fake.date()
        copy_2_date = fake.date()
        data = [
            {"workout_id": str(workout_1.id), "date": copy_1_date},
            {"workout_id": str(workout_2.id), "date": copy_2_date},
        ]

        response = await self._post_success("/copy", data=data)
        copied_workout_1_data = json.loads(
            await self.db.query_json(
                """
                SELECT Workout {id, name, date, exercises: {id, name, notes}}
                FILTER .name = <str>$name
                """,
                name=workout_1.name,
            )
        )
        copied_workout_2_data = json.loads(
            await self.db.query_json(
                """
                SELECT Workout {id, name, date, exercises: {id, name, notes}}
                FILTER .name = <str>$name
                """,
                name=workout_2.name,
            )
        )
        copied_workout_1_pair = [Workout(**d) for d in copied_workout_1_data]
        copied_workout_2_pair = [Workout(**d) for d in copied_workout_2_data]

        assert response.results
        assert len(response.results) == 2
        assert len(copied_workout_1_pair) == 2
        assert all(len(w.exercises) == len(workout_1.exercises) for w in copied_workout_1_pair)
        assert all(e in workout_1.exercises for w in copied_workout_1_pair for e in w.exercises)
        assert len(copied_workout_2_pair) == 2
        assert all(len(w.exercises) == len(workout_2.exercises) for w in copied_workout_2_pair)
        assert all(e in workout_2.exercises for w in copied_workout_2_pair for e in w.exercises)

    async def test_workout_copy_succeeds_when_updating_the_same_workout_with_different_dates(self) -> None:
        workout = await self.sample.workout()
        date_1 = fake.date()
        date_2 = fake.date()
        data = [
            {"workout_id": str(workout.id), "date": date_1},
            {"workout_id": str(workout.id), "date": date_2},
        ]

        response = await self._post_success("/copy", data=data)
        copied_workout_data = json.loads(
            await self.db.query_json(
                """
                SELECT Workout {id, name, date}
                FILTER .name = <str>$name
                """,
                name=workout.name,
            )
        )
        copied_workout_group = [Workout(**d) for d in copied_workout_data]

        assert response.results
        assert len(response.results) == 2
        assert len(copied_workout_data) == 3
        assert any(datetime.strptime(date_1, "%Y-%m-%d").date() == workout.date for workout in copied_workout_group)
        assert any(datetime.strptime(date_2, "%Y-%m-%d").date() == workout.date for workout in copied_workout_group)

    async def test_workout_copy_multiple_fails_when_copying_workout_belonging_to_other_user(self) -> None:
        workout = await self.sample.workout()
        workout_belonging_to_other_user = await self.sample.workout(user=await self.sample.user())
        data = [
            {"workout_id": str(workout.id), "date": fake.date()},
            {"workout_id": str(workout_belonging_to_other_user.id), "date": fake.date()},
        ]

        response = await self._post_error("/copy", data=data)

        assert response.message == NO_WORKOUT_FOUND

    async def _post_success(
        self, endpoint: str, data: dict[str, Any] | list[dict[str, Any]] | None = None
    ) -> SuccessResponse:
        response = SuccessResponse(**(await self.client.post(f"/api/v2/workouts{endpoint}", json=data or {})).json())
        assert response.code == "ok"
        return response

    async def _post_error(self, endpoint: str, data: dict[str, Any] | list[dict[str, Any]]) -> ErrorResponse:
        response = ErrorResponse(**(await self.client.post(f"/api/v2/workouts{endpoint}", json=data)).json())
        assert response.code == "error"
        return response
