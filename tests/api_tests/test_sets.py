from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

import pytest

from swole_v2.errors.messages import (
    CANNOT_BE_GREATER_THAN,
    INVALID_ID,
    MUST_BE_A_VALID_POSITIVE_INT,
    MUST_BE_POSITIVE,
    NO_EXERCISE_FOUND,
    NO_SET_FOUND,
    NO_WORKOUT_FOUND,
)
from swole_v2.models import SetRead
from swole_v2.schemas import ErrorResponse, SuccessResponse
from swole_v2.schemas.validators import MAX_REP_COUNT, MAX_WEIGHT

from .base import APITestBase, fake


class TestSets(APITestBase):
    invalid_set_data_params = (
        pytest.param(
            -fake.random_digit_not_null(),
            fake.random_digit_not_null(),
            MUST_BE_POSITIVE.format("rep_count"),
            id="Test negative rep count fails",
        ),
        pytest.param(
            fake.random_digit_not_null(),
            -fake.random_digit_not_null(),
            MUST_BE_POSITIVE.format("weight"),
            id="Test negative weight fails",
        ),
        pytest.param(
            501,
            fake.random_digit_not_null(),
            CANNOT_BE_GREATER_THAN.format(MAX_REP_COUNT),
            id="Test rep count greater than 500 fails",
        ),
        pytest.param(
            fake.random_digit_not_null(),
            10001,
            CANNOT_BE_GREATER_THAN.format(MAX_WEIGHT),
            id="Test weight greater than 10000 fails",
        ),
        pytest.param(fake.random_digit_not_null(), "  ", MUST_BE_A_VALID_POSITIVE_INT, id="Test blank weight fails"),
        pytest.param(fake.random_digit_not_null(), "", MUST_BE_A_VALID_POSITIVE_INT, id="Test empty weight fails"),
        pytest.param("", fake.random_digit_not_null(), MUST_BE_A_VALID_POSITIVE_INT, id="Test blank rep count fails"),
        pytest.param("", fake.random_digit_not_null(), MUST_BE_A_VALID_POSITIVE_INT, id="Test empty weight fails"),
    )

    invalid_set_id_params = (
        "set_id, message",
        [
            pytest.param(fake.random_digit(), INVALID_ID, id="Test non uuid fails"),
            pytest.param(uuid4(), NO_SET_FOUND, id="Test random uuid fails"),
        ],
    )

    async def test_set_get_all(self) -> None:
        workout = await self.sample.workout()
        exercise = await self.sample.exercise()
        sets = await self.sample.sets(workout=workout, exercise=exercise)

        response = await self._post_success(
            "/all", data={"workout_id": str(workout.id), "exercise_id": str(exercise.id)}
        )

        assert response.results
        assert response.results == [json.loads(SetRead(**s.model_dump()).model_dump_json()) for s in sets]

    async def test_set_get_all_only_returns_sets_owned_by_logged_in_user(self) -> None:
        user = await self.sample.user()
        workout = await self.sample.workout(user)
        exercise = await self.sample.exercise(user)
        await self.sample.sets(workout=workout, exercise=exercise)

        response = await self._post_success(
            "/all", data={"workout_id": str(workout.id), "exercise_id": str(exercise.id)}
        )

        assert response.results == []

    async def test_set_add_succeeds(self) -> None:
        rep_count = fake.random_digit_not_null()
        weight = fake.random_digit_not_null()
        workout = await self.sample.workout()
        exercise = await self.sample.exercise()
        data = {
            "workout_id": str(workout.id),
            "exercise_id": str(exercise.id),
            "rep_count": rep_count,
            "weight": weight,
        }

        response = await self._post_success("/add", [data])

        assert response.results
        assert "id" in response.results[0]
        assert ("rep_count", rep_count) in response.results[0].items()
        assert ("weight", weight) in response.results[0].items()

    async def test_set_add_multiple_succeeds(self) -> None:
        set_1_weight = fake.random_digit_not_null()
        set_1_rep_count = fake.random_digit_not_null()
        set_2_weight = fake.random_digit_not_null()
        set_2_rep_count = fake.random_digit_not_null()
        workout = await self.sample.workout()
        exercise = await self.sample.exercise()
        data = [
            {
                "workout_id": str(workout.id),
                "exercise_id": str(exercise.id),
                "rep_count": set_1_rep_count,
                "weight": set_1_weight,
            },
            # We want to be able to add the same information twice
            {
                "workout_id": str(workout.id),
                "exercise_id": str(exercise.id),
                "rep_count": set_1_rep_count,
                "weight": set_1_weight,
            },
            {
                "workout_id": str(workout.id),
                "exercise_id": str(exercise.id),
                "rep_count": set_2_rep_count,
                "weight": set_2_weight,
            },
        ]

        response = await self._post_success("/add", data=data)
        exercise_sets = json.loads(
            await self.db.query_single_json(
                """
                SELECT Exercise {sets := .<exercise[is ExerciseSet]}
                FILTER .id = <uuid>$exercise_id
                """,
                exercise_id=exercise.id,
            )
        )

        assert response.results
        assert len(exercise_sets["sets"]) == len(data)
        assert all("id" in result for result in response.results)
        assert any(("weight", set_1_weight) in results.items() for results in response.results)
        assert any(("rep_count", set_1_rep_count) in results.items() for results in response.results)
        assert any(("weight", set_2_weight) in results.items() for results in response.results)
        assert any(("rep_count", set_2_rep_count) in results.items() for results in response.results)

    async def test_set_add_fails_with_at_least_one_workout_belonging_to_another_user(self) -> None:
        weight = fake.random_digit_not_null()
        rep_count = fake.random_digit_not_null()
        workout = await self.sample.workout()
        workout_belonging_to_other_user = await self.sample.workout(user=await self.sample.user())
        exercise = await self.sample.exercise()
        data = [
            {
                "workout_id": str(workout.id),
                "exercise_id": str(exercise.id),
                "rep_count": rep_count,
                "weight": weight,
            },
            {
                "workout_id": str(workout_belonging_to_other_user.id),
                "exercise_id": str(exercise.id),
                "rep_count": rep_count,
                "weight": weight,
            },
        ]

        response = await self._post_error("/add", data=data)
        exercise_sets = json.loads(
            await self.db.query_single_json(
                """
                SELECT Exercise {sets := .<exercise[is ExerciseSet]}
                FILTER .id = <uuid>$exercise_id
                """,
                exercise_id=exercise.id,
            )
        )

        assert response.message == NO_WORKOUT_FOUND
        # Ensure no sets were added to the database
        assert len(exercise_sets["sets"]) == 0

    async def test_set_add_fails_with_at_least_one_exercise_belonging_to_another_user(self) -> None:
        weight = fake.random_digit_not_null()
        rep_count = fake.random_digit_not_null()
        workout = await self.sample.workout()
        exercise = await self.sample.exercise()
        exercise_belonging_to_other_user = await self.sample.exercise(user=await self.sample.user())
        data = [
            {
                "workout_id": str(workout.id),
                "exercise_id": str(exercise.id),
                "rep_count": rep_count,
                "weight": weight,
            },
            {
                "workout_id": str(workout.id),
                "exercise_id": str(exercise_belonging_to_other_user.id),
                "rep_count": rep_count,
                "weight": weight,
            },
        ]

        response = await self._post_error("/add", data=data)
        exercise_sets = json.loads(
            await self.db.query_single_json(
                """
                SELECT Exercise {sets := .<exercise[is ExerciseSet]}
                FILTER .id = <uuid>$exercise_id
                """,
                exercise_id=exercise.id,
            )
        )
        exercise_belonging_to_other_user_sets = json.loads(
            await self.db.query_single_json(
                """
                SELECT Exercise {sets := .<exercise[is ExerciseSet]}
                FILTER .id = <uuid>$exercise_id
                """,
                exercise_id=exercise_belonging_to_other_user.id,
            )
        )

        assert response.message == NO_EXERCISE_FOUND
        # Ensure no sets were added to the database
        assert len(exercise_sets["sets"]) == 0
        assert len(exercise_belonging_to_other_user_sets["sets"]) == 0

    async def test_set_add_fails_with_missing_required_value(self) -> None:
        workout = await self.sample.workout()
        exercise = await self.sample.exercise()
        data = [
            {
                "weight": fake.random_digit_not_null(),
                "exercise_id": str(exercise.id),
                "workout_id": str(workout.id),
            }
        ]

        response = await self._post_error("/add", data=data)

        assert response.message == "Field Required. Hint: (body > 0 > rep_count)."

    async def test_set_add_fails_with_exercise_belonging_to_other_user(self) -> None:
        rep_count = fake.random_digit_not_null()
        weight = fake.random_digit_not_null()
        workout = await self.sample.workout()
        exercise = await self.sample.exercise(user=await self.sample.user())
        data = {
            "workout_id": str(workout.id),
            "exercise_id": str(exercise.id),
            "rep_count": rep_count,
            "weight": weight,
        }

        response = await self._post_error("/add", [data])

        assert response.message == NO_EXERCISE_FOUND

    async def test_set_add_fails_with_workout_belonging_to_other_user(self) -> None:
        workout = await self.sample.workout(user=await self.sample.user())
        exercise = await self.sample.exercise()
        data = {
            "workout_id": str(workout.id),
            "exercise_id": str(exercise.id),
            "rep_count": fake.random_digit_not_null(),
            "weight": fake.random_digit_not_null(),
        }

        response = await self._post_error("/add", [data])

        assert response.message == NO_WORKOUT_FOUND

    @pytest.mark.parametrize(
        "rep_count, weight, message",
        [
            *invalid_set_data_params,
            pytest.param(
                None, fake.random_digit_not_null(), MUST_BE_A_VALID_POSITIVE_INT, id="Test no rep count fails"
            ),
            pytest.param(fake.random_digit_not_null(), None, MUST_BE_A_VALID_POSITIVE_INT, id="Test no weight fails"),
        ],
    )
    async def test_set_add_fails_with_invalid_data(self, rep_count: Any, weight: Any, message: str) -> None:
        workout = await self.sample.workout()
        exercise = await self.sample.exercise()
        data = {
            "workout_id": str(workout.id),
            "exercise_id": str(exercise.id),
            "rep_count": rep_count,
            "weight": weight,
        }

        response = await self._post_error("/add", [data])

        assert response.message == message

    @pytest.mark.parametrize(
        "workout_id, exercise_id, message",
        [
            pytest.param(fake.random_digit(), fake.random_digit(), INVALID_ID, id="Test non uuid fails."),
        ],
    )
    async def test_set_add_fails_with_invalid_ids(self, workout_id: Any, exercise_id: Any, message: str) -> None:
        data = {
            "workout_id": str(workout_id),
            "exercise_id": str(exercise_id),
            "rep_count": fake.random_digit_not_null(),
            "weight": fake.random_digit_not_null(),
        }

        response = await self._post_error("/add", [data])

        assert response.message == message

    async def test_set_delete_succeeds(self) -> None:
        set = await self.sample.set()
        data = {
            "set_id": str(set.id),
            "workout_id": str(set.workout.id),  # type: ignore
            "exercise_id": str(set.exercise.id),  # type: ignore
        }

        response = await self._post_success("/delete", data)

        post_set = json.loads(
            await self.db.query_single_json("SELECT ExerciseSet FILTER .id = <uuid>$set_id", set_id=set.id)
        )

        assert post_set is None
        assert response.results == []

    @pytest.mark.parametrize(*invalid_set_id_params)
    async def test_set_delete_fails_with_invalid_id(self, set_id: Any, message: str) -> None:
        response = await self._post_error("/delete", data={"set_id": str(set_id)})

        assert response.message == message

    async def test_cannot_delete_set_belonging_to_other_user(self) -> None:
        user = await self.sample.user()
        workout = await self.sample.workout(user)
        exercise = await self.sample.exercise(user)
        set = await self.sample.set(workout, exercise)
        data = {
            "set_id": str(set.id),
            "workout_id": str(workout.id),
            "exercise_id": str(exercise.id),
        }

        response = await self._post_error("/delete", data)

        await self.db.query_required_single_json("SELECT ExerciseSet FILTER .id = <uuid>$set_id", set_id=set.id)
        assert response.message == NO_SET_FOUND

    @pytest.mark.parametrize(
        "rep_count, weight",
        [
            pytest.param(fake.random_digit_not_null(), None, id="Test only update rep count succeeds."),
            pytest.param(None, fake.random_digit_not_null(), id="Test only update weight succeeds."),
            pytest.param(
                fake.random_digit_not_null(),
                fake.random_digit_not_null(),
                id="Test update both rep count and weight succeeds.",
            ),
        ],
    )
    async def test_set_update_succeeds(self, rep_count: int | None, weight: int | None) -> None:
        set = await self.sample.set()
        data = {
            "rep_count": rep_count,
            "weight": weight,
            "set_id": str(set.id),
            "workout_id": str(set.workout.id),  # type: ignore
            "exercise_id": str(set.exercise.id),  # type: ignore
        }

        response = await self._post_success("/update", data)

        assert response.results
        assert response.results == [
            {"id": str(set.id), "rep_count": rep_count or set.rep_count, "weight": weight or set.weight}
        ]

    @pytest.mark.parametrize("rep_count, weight, message", invalid_set_data_params)
    async def test_set_update_fails(self, rep_count: int | None, weight: int | None, message: str) -> None:
        set = await self.sample.set()
        data = {
            "rep_count": rep_count,
            "weight": weight,
            "set_id": str(set.id),
            "workout_id": str(set.workout.id),  # type: ignore
            "exercise_id": str(set.exercise.id),  # type: ignore
        }

        response = await self._post_error("/update", data)

        assert response.message == message

    @pytest.mark.parametrize(*invalid_set_id_params)
    async def test_set_update_fails_with_invalid_id(self, set_id: Any, message: str) -> None:
        data = {
            "rep_count": fake.random_digit_not_null(),
            "weight": fake.random_digit_not_null(),
            "set_id": str(set_id),
        }

        response = await self._post_error("/update", data)

        assert response.message == message

    async def _post_success(self, endpoint: str, data: dict[str, Any] | list[dict[str, Any]]) -> SuccessResponse:
        response = SuccessResponse(**(await self.client.post(f"/api/v2/sets{endpoint}", json=data)).json())
        assert response.code == "ok"
        return response

    async def _post_error(self, endpoint: str, data: dict[str, Any] | list[dict[str, Any]]) -> ErrorResponse:
        response = ErrorResponse(**(await self.client.post(f"/api/v2/sets{endpoint}", json=data)).json())
        assert response.code == "error"
        return response
