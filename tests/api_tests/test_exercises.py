from __future__ import annotations

import json
import random
from itertools import filterfalse
from statistics import mean
from typing import Any, Iterable
from uuid import uuid4

import pytest

from swole_v2.errors.messages import (
    EXERCISE_WITH_NAME_ALREADY_EXISTS,
    FIELD_CANNOT_BE_EMPTY,
    IDS_MUST_BE_UNIQUE,
    INVALID_ID,
    NO_EXERCISE_FOUND,
)
from swole_v2.models import Exercise, ExerciseRead
from swole_v2.schemas import ErrorResponse, SuccessResponse

from .base import APITestBase, fake


class TestExercises(APITestBase):
    invalid_exercise_id_params = (
        "exercise_id, message",
        [
            pytest.param(fake.random_digit(), INVALID_ID, id="Test non uuid id fails."),
            pytest.param(uuid4(), NO_EXERCISE_FOUND, id="Test random uuid id fails."),
        ],
    )

    invalid_name_params = (
        "name, message",
        [
            pytest.param("", FIELD_CANNOT_BE_EMPTY.format("name"), id="Test empty name fails."),
            pytest.param("   ", FIELD_CANNOT_BE_EMPTY.format("name"), id="Test blank name fails."),
        ],
    )

    async def test_exercise_get_all_succeeds(self) -> None:
        exercises = await self.sample.exercises()

        response = await self._post_success("/all")

        assert response.results
        assert len(response.results) == len(exercises)
        assert all(
            result in response.results
            for result in [json.loads(ExerciseRead(**e.model_dump()).model_dump_json()) for e in exercises]
        )

    async def test_exercise_get_all_returns_only_exercises_owned_by_logged_in_user(self) -> None:
        await self.sample.exercises(user=await self.sample.user())

        response = await self._post_success("/all")

        assert response.results == []

    async def test_exercise_detail_succeeds(self) -> None:
        exercise = await self.sample.exercise()

        response = await self._post_success("/detail", data=[{"exercise_id": str(exercise.id)}])

        assert response.results
        assert response.results == [{"id": str(exercise.id), "name": exercise.name, "notes": exercise.notes}]

    @pytest.mark.parametrize(*invalid_exercise_id_params)
    async def test_exercise_detail_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        response = await self._post_error("/detail", data=[{"exercise_id": str(exercise_id)}])
        assert response.message == message

    async def test_exercise_detail_multiple_succeeds(self) -> None:
        exercise_1 = await self.sample.exercise()
        exercise_2 = await self.sample.exercise()
        data = [
            {"exercise_id": str(exercise_1.id)},
            {"exercise_id": str(exercise_2.id)},
        ]

        response = await self._post_success("/detail", data=data)

        assert response.results
        assert len(response.results) == len(data)
        assert any(("id", str(exercise_1.id)) in results.items() for results in response.results)
        assert any(("name", exercise_1.name) in results.items() for results in response.results)
        assert any(("notes", exercise_1.notes) in results.items() for results in response.results)
        assert any(("id", str(exercise_2.id)) in results.items() for results in response.results)
        assert any(("name", exercise_2.name) in results.items() for results in response.results)
        assert any(("notes", exercise_2.notes) in results.items() for results in response.results)

    async def test_exercise_detail_fails_with_at_least_one_exercise_belonging_to_other_user(self) -> None:
        exercise = await self.sample.exercise()
        exercise_belonging_to_other_user = await self.sample.exercise(user=await self.sample.user())
        data = [
            {"exercise_id": str(exercise.id)},
            {"exercise_id": str(exercise_belonging_to_other_user.id)},
        ]

        response = await self._post_error("/detail", data=data)

        assert response.message == NO_EXERCISE_FOUND

    async def test_exercise_create_succeeds(self) -> None:
        name = fake.text()
        notes = fake.paragraph()
        data = {"name": name, "notes": notes}
        # Excercise with name exists but belongs to other user
        await self.sample.exercise(user=await self.sample.user(), name=name)

        response = await self._post_success("/create", data=[data])

        assert response.results
        assert "id" in response.results[0]
        assert ("name", name) in response.results[0].items()
        assert ("notes", notes) in response.results[0].items()

    @pytest.mark.parametrize(*invalid_name_params)
    async def test_exercise_create_with_invalid_name_fails(self, name: Any, message: str) -> None:
        response = await self._post_error("/create", data=[{"name": name}])

        assert response.message == message

    async def test_exercise_create_with_existing_name_fails(self) -> None:
        exercise = await self.sample.exercise()
        response = await self._post_error("/create", data=[{"name": exercise.name}])

        assert response.message == EXERCISE_WITH_NAME_ALREADY_EXISTS

    async def test_exercise_create_multiple_succeeds(self) -> None:
        name_1, notes_1 = fake.text(), fake.text()
        name_2, notes_2 = fake.text(), fake.text()
        data = [
            {"name": name_1, "notes": notes_1},
            {"name": name_2, "notes": notes_2},
        ]

        response = await self._post_success("/create", data=data)

        assert response.results
        assert len(response.results) == len(data)
        assert "id" in response.results[0]
        assert any(("name", name_1) in results.items() for results in response.results)
        assert any(("notes", notes_1) in results.items() for results in response.results)
        assert "id" in response.results[1]
        assert any(("name", name_2) in results.items() for results in response.results)
        assert any(("notes", notes_2) in results.items() for results in response.results)

    async def test_exercise_create_fails_when_trying_to_create_an_exercise_with_the_same_name_twice(self) -> None:
        common_name = fake.text()
        data = [
            {"name": common_name},
            {"name": common_name, "notes": fake.text()},
        ]

        response = await self._post_error("/create", data=data)

        assert response.message == EXERCISE_WITH_NAME_ALREADY_EXISTS

    @pytest.mark.parametrize(
        "name, notes",
        [
            pytest.param(fake.text(), fake.paragraph(), id="Test updating name and notes succeeds"),
            pytest.param(None, fake.paragraph(), id="Test updating only notes succeeds"),
            pytest.param(fake.text(), None, id="Test updating only name succeeds"),
            pytest.param(None, None, id="Test updating neither name nor notes succeeds"),
        ],
    )
    async def test_exercise_update_succeeds(self, name: str | None, notes: str | None) -> None:
        # Existing exercise with the new name but different user should work
        await self.sample.exercise(user=await self.sample.user(), name=name or fake.text())
        exercise = await self.sample.exercise()
        data = {"exercise_id": str(exercise.id), "name": name, "notes": notes}

        response = await self._post_success("/update", data=[data])
        updated_exercise = await self.db.query_required_single_json(
            """
            SELECT Exercise {id, name, notes}
            FILTER .id = <uuid>$exercise_id
            """,
            exercise_id=exercise.id,
        )

        assert response.results
        assert response.results == [json.loads(ExerciseRead.model_validate_json(updated_exercise).model_dump_json())]

    @pytest.mark.parametrize(*invalid_name_params)
    async def test_exercise_update_fails_with_invalid_name(self, name: Any, message: str) -> None:
        exercise = await self.sample.exercise()

        response = await self._post_error("/update", data=[{"exercise_id": str(exercise.id), "name": name}])

        assert response.message == message

    async def test_exercise_update_fails_with_existing_name_and_same_user(self) -> None:
        name = (await self.sample.exercise()).name
        exercise = await self.sample.exercise()

        response = await self._post_error("/update", data=[{"exercise_id": str(exercise.id), "name": name}])

        assert response.message == EXERCISE_WITH_NAME_ALREADY_EXISTS

    @pytest.mark.parametrize(*invalid_exercise_id_params)
    async def test_exercise_update_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        response = await self._post_error("/update", data=[{"exercise_id": str(exercise_id), "name": fake.text()}])

        assert response.message == message

    async def test_exercise_update_multiple_succeeds(self) -> None:
        exercise_1 = await self.sample.exercise()
        exercise_2 = await self.sample.exercise()
        new_name_1, new_notes_1 = fake.text(), fake.text()
        new_name_2, new_notes_2 = fake.text(), fake.text()
        data = [
            {"exercise_id": str(exercise_1.id), "name": new_name_1, "notes": new_notes_1},
            {"exercise_id": str(exercise_2.id), "name": new_name_2, "notes": new_notes_2},
        ]

        response = await self._post_success("/update", data=data)
        updated_exercise_1_data = json.loads(
            await self.db.query_single_json(
                "SELECT Exercise {id, name, notes} FILTER .id = <uuid>$exercise_id", exercise_id=exercise_1.id
            )
        )
        updated_exercise_1 = Exercise(**updated_exercise_1_data)
        updated_exercise_2_data = json.loads(
            await self.db.query_single_json(
                "SELECT Exercise {id, name, notes} FILTER .id = <uuid>$exercise_id", exercise_id=exercise_2.id
            )
        )
        updated_exercise_2 = Exercise(**updated_exercise_2_data)

        assert response.results
        assert len(response.results) == len(data)
        assert updated_exercise_1.name == new_name_1
        assert updated_exercise_1.notes == new_notes_1
        assert updated_exercise_2.name == new_name_2
        assert updated_exercise_2.notes == new_notes_2

    async def test_updating_the_same_exercise_multiple_times_in_the_same_request_fails(self) -> None:
        exercise = await self.sample.exercise()
        data = [
            {"exercise_id": str(exercise.id), "name": fake.text()},
            {"exercise_id": str(exercise.id), "notes": fake.text()},
        ]

        response = await self._post_error("/update", data=data)

        assert response.message == IDS_MUST_BE_UNIQUE

    async def test_updating_at_least_one_exercise_belonging_to_other_user_fails(self) -> None:
        exercise = await self.sample.exercise()
        exercise_belonging_to_other_user = await self.sample.exercise(user=await self.sample.user())
        data = [
            {"exercise_id": str(exercise.id), "name": fake.text()},
            {"exercise_id": str(exercise_belonging_to_other_user.id), "name": fake.text()},
        ]

        response = await self._post_error("/update", data=data)

        assert response.message == NO_EXERCISE_FOUND

    async def test_exercise_delete_succeeds(self) -> None:
        exercise = await self.sample.exercise()
        # Make sure we can delete an exercise that belongs to a workout
        await self.sample.workout(exercises=[exercise])

        response = await self._post_success("/delete", data=[{"exercise_id": str(exercise.id)}])
        deleted_exercise = json.loads(
            await self.db.query_single_json("SELECT Exercise FILTER .id = <uuid>$exercise_id", exercise_id=exercise.id)
        )

        assert deleted_exercise is None
        assert response.results == []

    @pytest.mark.parametrize(*invalid_exercise_id_params)
    async def test_exercise_delete_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        valid_exercise = await self.sample.exercise()
        data = [
            {"exercise_id": str(valid_exercise.id)},
            {"exercise_id": str(exercise_id)},
        ]
        response = await self._post_error("/delete", data=data)
        valid_exercise = json.loads(
            await self.db.query_single_json("SELECT Exercise FILTER .id = <uuid>$id", id=valid_exercise.id)
        )

        assert response.message == message
        assert valid_exercise is not None

    async def test_exercise_delete_multiple_succeeds(self) -> None:
        exercise_1 = await self.sample.exercise()
        exercise_2 = await self.sample.exercise()
        data = [
            {"exercise_id": str(exercise_1.id)},
            {"exercise_id": str(exercise_2.id)},
        ]

        response = await self._post_success("/delete", data=data)
        deleted_exercise_1 = json.loads(
            await self.db.query_single_json("SELECT Exercise FILTER .id = <uuid>$id", id=exercise_1.id)
        )
        deleted_exercise_2 = json.loads(
            await self.db.query_single_json("SELECT Exercise FILTER .id = <uuid>$id", id=exercise_2.id)
        )

        assert deleted_exercise_1 is None
        assert deleted_exercise_2 is None
        assert response.results == []

    async def test_exercise_delete_fails_when_at_least_one_exercise_belongs_to_other_user(self) -> None:
        exercise = await self.sample.exercise()
        exercise_belonging_to_other_user = await self.sample.exercise(user=await self.sample.user())
        data = [
            {"exercise_id": str(exercise.id)},
            {"exercise_id": str(exercise_belonging_to_other_user.id)},
        ]

        response = await self._post_error("/delete", data=data)

        assert response.message == NO_EXERCISE_FOUND

    async def test_exercise_progress_succeeds(self) -> None:
        exercise = await self.sample.exercise()
        exercise_set_groups = [
            set_group_1 := await self.sample.sets(exercise=exercise, size=random.choice(range(1, 10))),
            set_group_2 := await self.sample.sets(exercise=exercise, size=random.choice(range(1, 10))),
            set_group_3 := await self.sample.sets(exercise=exercise, size=random.choice(range(1, 10))),
        ]
        # Should not calculate other sets in same workout but different exercise
        await self.sample.sets(workout=set_group_1[0].workout)
        # Pass the same exercise twice to ensure it does not return double the expected results
        data = [
            {"exercise_id": str(exercise.id)},
            {"exercise_id": str(exercise.id)},
        ]

        response = await self._post_success("/progress", data=data)

        assert response.results
        assert len(response.results) == 1
        assert len(response.results[0]["data"]) == len(exercise_set_groups)
        assert response.results[0]["exercise_name"] == exercise.name
        assert response.results[0]["data"][0]["avg_rep_count"] == await self._rounded_mean(
            [g.rep_count for g in set_group_1]
        )
        assert response.results[0]["data"][1]["avg_rep_count"] == await self._rounded_mean(
            [g.rep_count for g in set_group_2]
        )
        assert response.results[0]["data"][2]["avg_rep_count"] == await self._rounded_mean(
            [g.rep_count for g in set_group_3]
        )
        assert response.results[0]["data"][0]["avg_weight"] == await self._rounded_mean([g.weight for g in set_group_1])
        assert response.results[0]["data"][1]["avg_weight"] == await self._rounded_mean([g.weight for g in set_group_2])
        assert response.results[0]["data"][2]["avg_weight"] == await self._rounded_mean([g.weight for g in set_group_3])
        assert response.results[0]["data"][0]["max_weight"] == max([g.weight for g in set_group_1])
        assert response.results[0]["data"][1]["max_weight"] == max([g.weight for g in set_group_2])
        assert response.results[0]["data"][2]["max_weight"] == max([g.weight for g in set_group_3])
        assert response.results[0]["data"][0]["date"] == set_group_1[0].workout.date.strftime("%Y-%m-%d")  # type: ignore
        assert response.results[0]["data"][1]["date"] == set_group_2[0].workout.date.strftime("%Y-%m-%d")  # type: ignore
        assert response.results[0]["data"][2]["date"] == set_group_3[0].workout.date.strftime("%Y-%m-%d")  # type: ignore

    @pytest.mark.parametrize(*invalid_exercise_id_params)
    async def test_exercise_progress_fails_with_invalid_id(self, exercise_id: Any, message: str) -> None:
        response = await self._post_error("/progress", data=[{"exercise_id": str(exercise_id)}])

        assert response.message == message

    async def test_exercise_progress_multiple_succeeds(self) -> None:
        exercise_1 = await self.sample.exercise()
        exercise_1_set_groups = [
            await self.sample.sets(exercise=exercise_1, size=random.choice(range(1, 10))),
            await self.sample.sets(exercise=exercise_1, size=random.choice(range(1, 10))),
        ]
        exercise_2 = await self.sample.exercise()
        data = [
            {"exercise_id": str(exercise_1.id)},
            {"exercise_id": str(exercise_2.id)},
        ]

        response = await self._post_success("/progress", data=data)

        assert response.results
        assert len(response.results) == len(data)
        exercise_1_progress_report = next(
            iter(filterfalse(lambda r: r["exercise_name"] != exercise_1.name, response.results))
        )
        exercise_2_progress_report = next(
            iter(filterfalse(lambda r: r["exercise_name"] != exercise_2.name, response.results))
        )
        assert len(exercise_1_progress_report["data"]) == len(exercise_1_set_groups)
        assert len(exercise_2_progress_report["data"]) == 0  # no sets were added to exercise 2

    async def test_exercise_progress_fails_when_using_an_exercise_id_belonging_to_another_user(self) -> None:
        exercise = await self.sample.exercise()
        exercise_belonging_to_other_user = await self.sample.exercise(user=await self.sample.user())
        data = [
            {"exercise_id": str(exercise.id)},
            {"exercise_id": str(exercise_belonging_to_other_user.id)},
        ]

        response = await self._post_error("/progress", data=data)

        assert response.message == NO_EXERCISE_FOUND

    async def test_exercise_progress_returns_empty_list_when_exercise_has_no_sets(self) -> None:
        exercise = await self.sample.exercise()
        response = await self._post_success("/progress", data=[{"exercise_id": str(exercise.id)}])

        assert response.results == []

    async def _post_success(
        self, endpoint: str, data: dict[str, Any] | list[dict[str, Any]] | None = None
    ) -> SuccessResponse:
        response = SuccessResponse(**(await self.client.post(f"/api/v2/exercises{endpoint}", json=data or {})).json())
        assert response.code == "ok"
        return response

    async def _post_error(self, endpoint: str, data: dict[str, Any] | list[dict[str, Any]]) -> ErrorResponse:
        response = ErrorResponse(**(await self.client.post(f"/api/v2/exercises{endpoint}", json=data)).json())
        assert response.code == "error"
        return response

    async def _rounded_mean(self, iterable: Iterable[int], decimal_places: int = 2) -> float:
        return round(mean(iterable), decimal_places)
