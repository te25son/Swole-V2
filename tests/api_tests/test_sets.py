from typing import Any
from uuid import uuid4

import pytest
from sqlmodel import select

from swole_v2.errors.messages import (
    INVALID_ID,
    MUST_BE_A_NON_NEGATIVE_NUMBER,
    MUST_BE_A_VALID_NON_NEGATIVE_NUMBER,
    MUST_BE_LESS_THAN,
    NO_SET_FOUND,
    NO_WORKOUT_AND_EXERCISE_LINK_FOUND,
)
from swole_v2.models import Set, SetRead, WorkoutExerciseLink
from swole_v2.schemas import ErrorResponse, SuccessResponse

from .base import APITestBase, fake, sample


class TestSets(APITestBase):
    invalid_set_data_params = [
        pytest.param(
            -fake.random_digit_not_null(),
            fake.random_digit_not_null(),
            MUST_BE_A_NON_NEGATIVE_NUMBER,
            id="Test negative rep count fails",
        ),
        pytest.param(
            fake.random_digit_not_null(),
            -fake.random_digit_not_null(),
            MUST_BE_A_NON_NEGATIVE_NUMBER,
            id="Test negative weight fails",
        ),
        pytest.param(
            501,
            fake.random_digit_not_null(),
            MUST_BE_LESS_THAN.format(501),
            id="Test rep count greater than 500 fails",
        ),
        pytest.param(
            fake.random_digit_not_null(),
            10001,
            MUST_BE_LESS_THAN.format(10001),
            id="Test weight greater than 10000 fails",
        ),
        pytest.param(
            fake.random_digit_not_null(), "  ", MUST_BE_A_VALID_NON_NEGATIVE_NUMBER, id="Test blank weight fails"
        ),
        pytest.param(
            fake.random_digit_not_null(), "", MUST_BE_A_VALID_NON_NEGATIVE_NUMBER, id="Test empty weight fails"
        ),
        pytest.param(
            "", fake.random_digit_not_null(), MUST_BE_A_VALID_NON_NEGATIVE_NUMBER, id="Test blank rep count fails"
        ),
        pytest.param(
            "", fake.random_digit_not_null(), MUST_BE_A_VALID_NON_NEGATIVE_NUMBER, id="Test empty weight fails"
        ),
    ]

    invalid_set_id_params = (
        "workout_id, exercise_id, set_id, message",
        [
            pytest.param(uuid4(), uuid4(), uuid4(), NO_SET_FOUND, id="Test random uuid fails."),
            pytest.param(
                fake.random_digit(), fake.random_digit(), fake.random_digit(), INVALID_ID, id="Test non uuid fails."
            ),
            pytest.param(
                (set := sample.set()).id,
                set.workout_id,  # type: ignore
                set.exercise_id,  # type: ignore
                NO_SET_FOUND,
                id="Test set belonging to other user fails.",
            ),
        ],
    )

    def test_set_get_all(self) -> None:
        link = self.sample.workout_exercise_link()
        sets = self.sample.sets(link=link)

        response = SuccessResponse(
            **self.client.post(
                "/sets/all", json={"workout_id": str(link.workout_id), "exercise_id": str(link.exercise_id)}
            ).json()
        )

        assert response.results
        assert response.code == "ok"
        assert response.results == [SetRead(**s.dict()).dict() for s in sets]

    def test_set_get_all_only_returns_sets_owned_by_logged_in_user(self) -> None:
        link = self.sample.workout_exercise_link(user=self.sample.user())
        self.sample.sets(link=link)

        response = ErrorResponse(
            **self.client.post(
                "/sets/all", json={"workout_id": str(link.workout_id), "exercise_id": str(link.exercise_id)}
            ).json()
        )

        assert response.code == "error"
        assert response.message == NO_WORKOUT_AND_EXERCISE_LINK_FOUND

    def test_set_add_succeeds(self) -> None:
        rep_count = fake.random_digit_not_null()
        weight = fake.random_digit_not_null()
        link = self.sample.workout_exercise_link()
        data = {
            "workout_id": str(link.workout_id),
            "exercise_id": str(link.exercise_id),
            "rep_count": rep_count,
            "weight": weight,
        }

        response = SuccessResponse(**self.client.post("/sets/add", json=data).json())

        assert response.results
        assert response.code == "ok"
        assert response.results == [{"rep_count": rep_count, "weight": weight}]

    def test_set_add_fails_with_exercise_belonging_to_other_user(self) -> None:
        rep_count = fake.random_digit_not_null()
        weight = fake.random_digit_not_null()
        workout = self.sample.workout()
        exercise = self.sample.exercise(user=self.sample.user())
        data = {
            "workout_id": str(workout.id),
            "exercise_id": str(exercise.id),
            "rep_count": rep_count,
            "weight": weight,
        }

        response = ErrorResponse(**self.client.post("/sets/add", json=data).json())

        assert response.code == "error"
        assert response.message == NO_WORKOUT_AND_EXERCISE_LINK_FOUND

    def test_set_add_fails_with_workout_belonging_to_other_user(self) -> None:
        workout = self.sample.workout(user=self.sample.user())
        exercise = self.sample.exercise()
        data = {
            "workout_id": str(workout.id),
            "exercise_id": str(exercise.id),
            "rep_count": fake.random_digit_not_null(),
            "weight": fake.random_digit_not_null(),
        }

        response = ErrorResponse(**self.client.post("/sets/add", json=data).json())

        assert response.code == "error"
        assert response.message == NO_WORKOUT_AND_EXERCISE_LINK_FOUND

    def test_set_add_fails_with_workout_and_exercise_that_are_owned_by_logged_in_user_but_are_not_linked(self) -> None:
        workout = self.sample.workout()
        exercise = self.sample.exercise()
        data = {
            "workout_id": str(workout.id),
            "exercise_id": str(exercise.id),
            "rep_count": fake.random_digit_not_null(),
            "weight": fake.random_digit_not_null(),
        }

        response = ErrorResponse(**self.client.post("/sets/add", json=data).json())

        assert response.code == "error"
        assert response.message == NO_WORKOUT_AND_EXERCISE_LINK_FOUND

    @pytest.mark.parametrize(
        "rep_count, weight, message",
        invalid_set_data_params
        + [
            pytest.param(
                None,
                fake.random_digit_not_null(),
                MUST_BE_A_VALID_NON_NEGATIVE_NUMBER,
                id="Test no rep count fails",
            ),
            pytest.param(
                fake.random_digit_not_null(), None, MUST_BE_A_VALID_NON_NEGATIVE_NUMBER, id="Test no weight fails"
            ),
        ],
    )
    def test_set_add_fails_with_invalid_data(self, rep_count: Any, weight: Any, message: str) -> None:
        link = self.sample.workout_exercise_link()
        data = {
            "workout_id": str(link.workout_id),
            "exercise_id": str(link.exercise_id),
            "rep_count": rep_count,
            "weight": weight,
        }

        response = ErrorResponse(**self.client.post("/sets/add", json=data).json())

        assert response.code == "error"
        assert response.message == message

    @pytest.mark.parametrize(
        "workout_id, exercise_id, message",
        [
            pytest.param(uuid4(), uuid4(), NO_WORKOUT_AND_EXERCISE_LINK_FOUND, id="Test random uuid fails."),
            pytest.param(fake.random_digit(), fake.random_digit(), INVALID_ID, id="Test non uuid fails."),
            pytest.param(
                (link := sample.workout_exercise_link()).workout_id,
                link.exercise_id,  # type: ignore
                NO_WORKOUT_AND_EXERCISE_LINK_FOUND,
                id="Test workout and exercise belonging to other user fails.",
            ),
        ],
    )
    def test_set_add_fails_with_invalid_ids(self, workout_id: Any, exercise_id: Any, message: str) -> None:
        data = {
            "workout_id": str(workout_id),
            "exercise_id": str(exercise_id),
            "rep_count": fake.random_digit_not_null(),
            "weight": fake.random_digit_not_null(),
        }

        response = ErrorResponse(**self.client.post("/sets/add", json=data).json())

        assert response.code == "error"
        assert response.message == message

    def test_set_delete_succeeds(self) -> None:
        set = self.sample.set()
        data = {
            "set_id": str(set.id),
            "workout_id": str(set.workout_id),
            "exercise_id": str(set.exercise_id),
        }

        response = SuccessResponse(**self.client.post("/sets/delete", json=data).json())

        link = self.session.exec(
            select(WorkoutExerciseLink)
            .where(WorkoutExerciseLink.workout_id == set.workout_id)
            .where(WorkoutExerciseLink.exercise_id == set.exercise_id)
        ).one()
        post_set = self.session.exec(select(Set).where(Set.id == set.id)).one_or_none()

        assert set not in link.sets
        assert post_set is None
        assert response.code == "ok"
        assert response.results == None

    @pytest.mark.parametrize(*invalid_set_id_params)
    def test_set_delete_fails(self, set_id: Any, workout_id: Any, exercise_id: Any, message: str) -> None:
        data = {
            "set_id": str(set_id),
            "workout_id": str(workout_id),
            "exercise_id": str(exercise_id),
        }

        response = ErrorResponse(**self.client.post("/sets/delete", json=data).json())

        assert response.code == "error"
        assert response.message == message

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
    def test_set_update_succeeds(self, rep_count: int | None, weight: int | None) -> None:
        set = self.sample.set()
        data = {
            "rep_count": rep_count,
            "weight": weight,
            "set_id": str(set.id),
            "workout_id": str(set.workout_id),
            "exercise_id": str(set.exercise_id),
        }

        response = SuccessResponse(**self.client.post("/sets/update", json=data).json())

        assert response.results
        assert response.code == "ok"
        assert response.results == [{"rep_count": rep_count or set.rep_count, "weight": weight or set.weight}]

    @pytest.mark.parametrize("rep_count, weight, message", invalid_set_data_params)
    def test_set_update_fails(self, rep_count: int | None, weight: int | None, message: str) -> None:
        set = self.sample.set()
        data = {
            "rep_count": rep_count,
            "weight": weight,
            "set_id": str(set.id),
            "workout_id": str(set.workout_id),
            "exercise_id": str(set.exercise_id),
        }

        response = ErrorResponse(**self.client.post("/sets/update", json=data).json())

        assert response.code == "error"
        assert response.message == message

    @pytest.mark.parametrize(*invalid_set_id_params)
    def test_set_update_fails_with_invalid_ids(self, set_id: Any, workout_id: Any, exercise_id: Any, message: str) -> None:
        data = {
            "rep_count": fake.random_digit_not_null(),
            "weight": fake.random_digit_not_null(),
            "set_id": str(set_id),
            "workout_id": str(workout_id),
            "exercise_id": str(exercise_id),
        }

        response = ErrorResponse(**self.client.post("/sets/update", json=data).json())

        assert response.code == "error"
        assert response.message == message
