import json
from typing import Any
from uuid import uuid4

import pytest

from swole_v2.errors.messages import (
    EXERCISE_WITH_NAME_ALREADY_EXISTS,
    FIELD_CANNOT_BE_EMPTY,
    INVALID_ID,
    NO_EXERCISE_FOUND,
)
from swole_v2.models import ExerciseRead
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
        assert all(result in response.results for result in [ExerciseRead(**e.dict()).dict() for e in exercises])

    async def test_exercise_get_all_returns_only_exercises_owned_by_logged_in_user(self) -> None:
        await self.sample.exercises(user=await self.sample.user())

        response = await self._post_success("/all")

        assert response.results == []

    async def test_exercise_detail_succeeds(self) -> None:
        exercise = await self.sample.exercise()

        response = await self._post_success("/detail", data={"exercise_id": str(exercise.id)})

        assert response.results
        assert response.results == [{"name": exercise.name, "notes": exercise.notes}]

    @pytest.mark.parametrize(*invalid_exercise_id_params)
    async def test_exercise_detail_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        response = await self._post_error("/detail", data={"exercise_id": str(exercise_id)})
        assert response.message == message

    async def test_exercise_create_succeeds(self) -> None:
        name = fake.text()
        notes = fake.paragraph()
        data = {"name": name, "notes": notes}
        # Excercise with name exists but belongs to other user
        await self.sample.exercise(user=await self.sample.user(), name=name)

        response = await self._post_success("/create", data=data)

        assert response.results
        assert response.results == [data]

    @pytest.mark.parametrize(*invalid_name_params)
    async def test_exercise_create_with_invalid_name_fails(self, name: Any, message: str) -> None:
        response = await self._post_error("/create", data={"name": name})

        assert response.message == message

    async def test_exercise_create_with_existing_name_fails(self) -> None:
        exercise = await self.sample.exercise()
        response = await self._post_error("/create", data={"name": exercise.name})

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

        response = await self._post_success("/update", data=data)
        updated_exercise = await self.db.query_required_single_json(
            """
            SELECT Exercise {name, notes}
            FILTER .id = <uuid>$exercise_id
            """,
            exercise_id=exercise.id,
        )

        assert response.results
        assert response.results == [ExerciseRead.parse_raw(updated_exercise).dict()]

    @pytest.mark.parametrize(*invalid_name_params)
    async def test_exercise_update_fails_with_invalid_name(self, name: Any, message: str) -> None:
        exercise = await self.sample.exercise()

        response = await self._post_error("/update", data={"exercise_id": str(exercise.id), "name": name})

        assert response.message == message

    async def test_exercise_update_fails_with_existing_name_and_same_user(self) -> None:
        name = (await self.sample.exercise()).name
        exercise = await self.sample.exercise()

        response = await self._post_error("/update", data={"exercise_id": str(exercise.id), "name": name})

        assert response.message == EXERCISE_WITH_NAME_ALREADY_EXISTS

    @pytest.mark.parametrize(*invalid_exercise_id_params)
    async def test_exercise_update_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        response = await self._post_error("/update", data={"exercise_id": str(exercise_id), "name": fake.text()})

        assert response.message == message

    async def test_exercise_delete_succeeds(self) -> None:
        exercise = await self.sample.exercise()

        response = await self._post_success("/delete", data={"exercise_id": str(exercise.id)})
        deleted_exercise = json.loads(
            await self.db.query_single_json("SELECT Exercise FILTER .id = <uuid>$exercise_id", exercise_id=exercise.id)
        )

        assert deleted_exercise is None
        assert response.results is None

    @pytest.mark.parametrize(*invalid_exercise_id_params)
    async def test_exercise_delete_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        response = await self._post_error("/delete", data={"exercise_id": str(exercise_id)})

        assert response.message == message

    async def _post_success(self, endpoint: str, data: dict[str, Any] = {}) -> SuccessResponse:
        response = SuccessResponse(**(await self.client.post(f"/api/v2/exercises{endpoint}", json=data)).json())
        assert response.code == "ok"
        return response

    async def _post_error(self, endpoint: str, data: dict[str, Any]) -> ErrorResponse:
        response = ErrorResponse(**(await self.client.post(f"/api/v2/exercises{endpoint}", json=data)).json())
        assert response.code == "error"
        return response
