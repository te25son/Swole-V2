from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any

from edgedb import CardinalityViolationError, ConstraintViolationError

from ...errors.exceptions import BusinessError
from ...errors.messages import EXERCISE_WITH_NAME_ALREADY_EXISTS, IDS_MUST_BE_UNIQUE, NO_EXERCISE_FOUND
from ...models import ExerciseProgressReport, ExerciseRead
from .base import BaseRepository

if TYPE_CHECKING:
    from uuid import UUID

    from ...schemas import ExerciseCreate, ExerciseDelete, ExerciseDetail, ExerciseProgress, ExerciseUpdate


class ExerciseRepository(BaseRepository):
    async def get_all(self, user_id: UUID | None) -> list[ExerciseRead]:
        exercises = await self.query_json(
            """
            SELECT Exercise {id, name, notes}
            FILTER .user.id = <uuid>$user_id
            """,
            user_id=user_id,
        )
        return [ExerciseRead(**exercise) for exercise in exercises]

    async def detail(self, user_id: UUID | None, data: list[ExerciseDetail]) -> list[ExerciseRead]:
        try:
            exercises = await self.query_json(
                """
                WITH exercises := (
                    FOR data IN array_unpack(<array<json>>$data) UNION assert_exists((
                        SELECT Exercise
                        FILTER .id = <uuid>data['exercise_id'] AND .user.id = <uuid>$user_id
                    ))
                )
                SELECT exercises {id, name, notes}
                """,
                data=data,
                user_id=user_id,
            )
            return [ExerciseRead(**exercise) for exercise in exercises]
        except CardinalityViolationError as error:
            raise BusinessError(NO_EXERCISE_FOUND) from error

    async def create(self, user_id: UUID | None, data: list[ExerciseCreate]) -> list[ExerciseRead]:
        try:
            exercises = await self.query_json(
                """
                WITH exercises := (
                    FOR data IN array_unpack(<array<json>>$data) UNION (
                        INSERT Exercise {
                            name := <str>data['name'],
                            notes := <optional str>data['notes'],
                            user := (
                                SELECT User
                                FILTER .id = <uuid>$user_id
                            )
                        }
                    )
                )
                SELECT exercises {id, name, notes}
                """,
                data=data,
                user_id=user_id,
            )
            return [ExerciseRead(**exercise) for exercise in exercises]
        except ConstraintViolationError as error:
            raise BusinessError(EXERCISE_WITH_NAME_ALREADY_EXISTS) from error

    async def update(self, user_id: UUID | None, data: list[ExerciseUpdate]) -> list[ExerciseRead]:
        try:
            if len({d.exercise_id for d in data}) != len(data):
                raise BusinessError(IDS_MUST_BE_UNIQUE)

            exercises = await self.query_json(
                """
                WITH exercises := (
                    FOR data IN array_unpack(<array<json>>$data) UNION assert_exists((
                        UPDATE Exercise
                        FILTER .id = <uuid>data['exercise_id'] AND .user.id = <uuid>$user_id
                        SET {
                            name := <optional str>data['name'] ?? .name,
                            notes := <optional str>data['notes'] ?? .notes
                        }
                    ))
                )
                SELECT exercises {id, name, notes}
                """,
                data=data,
                user_id=user_id,
            )
            return [ExerciseRead(**exercise) for exercise in exercises]
        except CardinalityViolationError as error:
            raise BusinessError(NO_EXERCISE_FOUND) from error
        except ConstraintViolationError as error:
            raise BusinessError(EXERCISE_WITH_NAME_ALREADY_EXISTS) from error

    async def delete(self, user_id: UUID | None, data: list[ExerciseDelete]) -> None:
        try:
            await self.query_json(
                """
                WITH exercises := (
                    FOR data IN array_unpack(<array<json>>$data) UNION assert_exists((
                        SELECT Exercise
                        FILTER .id = <uuid>data['exercise_id'] AND .user.id = <uuid>$user_id
                    ))
                )
                DELETE exercises
                """,
                data=data,
                user_id=user_id,
            )
        except CardinalityViolationError as error:
            raise BusinessError(NO_EXERCISE_FOUND) from error

    async def progress(self, user_id: UUID | None, data: list[ExerciseProgress]) -> list[ExerciseProgressReport]:
        try:
            exercises = await self.query_json(
                """
                WITH exercises := (
                    FOR data IN array_unpack(<array<json>>$data) UNION assert_exists((
                        SELECT Exercise
                        FILTER .id = <uuid>data['exercise_id'] AND .user.id = <uuid>$user_id
                    ))
                )
                SELECT exercises {id, name}
                """,
                data=data,
                user_id=user_id,
            )
            progress_results = await self.query_json(
                """
                WITH grouped_exercise_sets := (
                    GROUP (
                        FOR data IN array_unpack(<array<json>>$data) UNION (
                            SELECT ExerciseSet
                            FILTER .exercise.id = <uuid>data['exercise_id'] AND .exercise.user.id = <uuid>$user_id
                        )
                    ) BY (.workout, .exercise)
                )
                SELECT grouped_exercise_sets {
                    name := .key.exercise.name,
                    date := .key.workout.date,
                    avg_rep_count := math::mean(.elements.rep_count),
                    avg_weight := math::mean(.elements.weight),
                    max_weight := max(.elements.weight)
                }
                """,
                data=data,
                user_id=user_id,
            )
            progress_by_exercise = await self._join_progress_data_and_exercises_by_exercise_name(
                exercises, progress_results
            )
            progress_reports = [
                {"exercise_name": exercise_name, "data": data_list}
                for exercise_name, data_list in progress_by_exercise.items()
            ]
            return [ExerciseProgressReport(**report) for report in progress_reports]
        except CardinalityViolationError as error:
            raise BusinessError(NO_EXERCISE_FOUND) from error

    @staticmethod
    async def _join_progress_data_and_exercises_by_exercise_name(
        exercises: list[dict[str, Any]], progress_data: list[dict[str, Any]]
    ) -> dict[str, Any]:
        progress_by_exercise = defaultdict(list)
        for exercise in exercises:
            exercise_name = exercise["name"]
            for data in progress_data:
                if exercise_name == data["name"]:
                    progress_by_exercise[exercise_name].append(data)
                else:
                    progress_by_exercise[exercise_name]
        return progress_by_exercise
