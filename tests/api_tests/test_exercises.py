import json
from typing import Any

import pytest

from swole_v2.errors.messages import (
    EXERCISE_WITH_NAME_ALREADY_EXISTS,
    FIELD_CANNOT_BE_EMPTY,
    INVALID_ID,
)
from swole_v2.models import ExerciseRead
from swole_v2.schemas import ErrorResponse, SuccessResponse

from .base import APITestBase, fake


class TestExercises(APITestBase):
    invalid_exercise_id_params = (
        "exercise_id, message",
        [
            pytest.param(fake.random_digit(), INVALID_ID, id="Test non uuid id fails."),
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

    async def test_exercise_get_all_succeeds(self) -> None:
        exercises = await self.sample.exercises()

        response = SuccessResponse(**(await self.client.post("/exercises/all")).json())

        assert response.results
        assert response.code == "ok"
        assert len(response.results) == len(exercises)
        assert all(result in response.results for result in [ExerciseRead(**e.dict()).dict() for e in exercises])

    async def test_exercise_get_all_returns_only_exercises_owned_by_logged_in_user(self) -> None:
        await self.sample.exercises(user=await self.sample.user())

        response = SuccessResponse(**(await self.client.post("/exercises/all")).json())

        assert response.code == "ok"
        assert response.results == []

    async def test_exercise_detail_succeeds(self) -> None:
        exercise = await self.sample.exercise()

        response = SuccessResponse(
            **(await self.client.post("/exercises/detail", json={"exercise_id": str(exercise.id)})).json()
        )

        assert response.results
        assert response.code == "ok"
        assert response.results == [{"name": exercise.name, "notes": exercise.notes}]

    @pytest.mark.parametrize(*invalid_exercise_id_params)
    async def test_exercise_detail_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        response = ErrorResponse(
            **(await self.client.post("/exercises/detail", json={"exercise_id": str(exercise_id)})).json()
        )

        assert response.code == "error"
        assert response.message == message

    async def test_exercise_create_succeeds(self) -> None:
        name = fake.text()
        notes = fake.paragraph()
        data = {"name": name, "notes": notes}
        # Excercise with name exists but belongs to other user
        await self.sample.exercise(user=await self.sample.user(), name=name)

        response = SuccessResponse(**(await self.client.post("/exercises/create", json=data)).json())

        assert response.results
        assert response.code == "ok"
        assert response.results == [data]

    @pytest.mark.parametrize(*invalid_name_params)
    async def test_exercise_create_with_invalid_name_fails(self, name: Any, message: str) -> None:
        response = ErrorResponse(**(await self.client.post("/exercises/create", json={"name": name})).json())

        assert response.code == "error"
        assert response.message == message

    async def test_exercise_create_with_existing_name_fails(self) -> None:
        exercise = await self.sample.exercise()

        response = ErrorResponse(**(await self.client.post("/exercises/create", json={"name": exercise.name})).json())

        assert response.code == "error"
        assert response.message == EXERCISE_WITH_NAME_ALREADY_EXISTS

    async def test_exercise_add_succeeds(self) -> None:
        workout = await self.sample.workout()
        exercise = await self.sample.exercise()
        data = {"workout_id": str(workout.id), "exercise_id": str(exercise.id)}

        response = SuccessResponse(**(await self.client.post("/exercises/add", json=data)).json())

        assert response.results
        assert response.code == "ok"
        assert response.results == [ExerciseRead(**exercise.dict()).dict()]

    @pytest.mark.parametrize(
        "workout_id, message",
        [pytest.param(fake.random_digit(), INVALID_ID, id="Test random digit fails.")],
    )
    async def test_exercise_add_fails_with_invalid_workout_id(self, workout_id: Any, message: str) -> None:
        # Ensure the user has workouts but none matching the given id
        await self.sample.workouts()
        exercise = await self.sample.exercise()
        data = {"workout_id": str(workout_id), "exercise_id": str(exercise.id)}

        response = ErrorResponse(**(await self.client.post("/exercises/add", json=data)).json())

        assert response.code == "error"
        assert response.message == message

    @pytest.mark.parametrize(
        "exercise_id, message",
        [
            pytest.param(fake.random_digit(), INVALID_ID, id="Test random digit fails."),
        ],
    )
    async def test_exercise_add_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        # Ensure the user has exercises but none matching the given id
        await self.sample.exercises()
        workout = await self.sample.workout()
        data = {"workout_id": str(workout.id), "exercise_id": str(exercise_id)}

        response = ErrorResponse(**(await self.client.post("/exercises/add", json=data)).json())

        assert response.code == "error"
        assert response.message == message

    async def test_exercise_update_succeeds(self) -> None:
        new_name = fake.text()
        new_notes = fake.paragraph()
        # Existing exercise with the new name but different user should work
        await self.sample.exercise(user=await self.sample.user(), name=new_name)
        exercise = await self.sample.exercise()
        data = {"exercise_id": str(exercise.id), "name": new_name, "notes": new_notes}

        response = SuccessResponse(**(await self.client.post("/exercises/update", json=data)).json())
        updated_exercise = await self.db.query_required_single_json(
            """
            SELECT Exercise {name, notes}
            FILTER .id = <uuid>$exercise_id
            """,
            exercise_id=exercise.id,
        )

        assert response.results
        assert response.code == "ok"
        assert response.results == [ExerciseRead.parse_raw(updated_exercise).dict()]

    @pytest.mark.parametrize(*invalid_name_params)
    async def test_exercise_update_fails_with_invalid_name(self, name: Any, message: str) -> None:
        exercise = await self.sample.exercise()

        response = ErrorResponse(
            **(await self.client.post("/exercises/update", json={"exercise_id": str(exercise.id), "name": name})).json()
        )

        assert response.code == "error"
        assert response.message == message

    async def test_exercise_update_fails_with_existing_name_and_same_user(self) -> None:
        name = (await self.sample.exercise()).name
        exercise = await self.sample.exercise()

        response = ErrorResponse(
            **(await self.client.post("/exercises/update", json={"exercise_id": str(exercise.id), "name": name})).json()
        )

        assert response.code == "error"
        assert response.message == EXERCISE_WITH_NAME_ALREADY_EXISTS

    @pytest.mark.parametrize(*invalid_exercise_id_params)
    async def test_exercise_update_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        response = ErrorResponse(
            **(
                await self.client.post("/exercises/update", json={"exercise_id": str(exercise_id), "name": fake.text()})
            ).json()
        )

        assert response.code == "error"
        assert response.message == message

    async def test_exercise_delete_succeeds(self) -> None:
        exercise = await self.sample.exercise()

        response = SuccessResponse(
            **(await self.client.post("exercises/delete", json={"exercise_id": str(exercise.id)})).json()
        )
        deleted_exercise = json.loads(
            await self.db.query_single_json("SELECT Exercise FILTER .id = <uuid>$exercise_id", exercise_id=exercise.id)
        )

        assert deleted_exercise is None
        assert response.code == "ok"
        assert response.results is None

    @pytest.mark.parametrize(*invalid_exercise_id_params)
    async def test_exercise_delete_fails_with_invalid_exercise_id(self, exercise_id: Any, message: str) -> None:
        response = ErrorResponse(
            **(await self.client.post("/exercises/delete", json={"exercise_id": str(exercise_id)})).json()
        )

        assert response.code == "error"
        assert response.message == message
