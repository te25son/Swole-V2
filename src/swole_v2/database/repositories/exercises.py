from __future__ import annotations

import json
from typing import TYPE_CHECKING

from edgedb import CardinalityViolationError, ConstraintViolationError

from ...errors.exceptions import BusinessError
from ...errors.messages import EXERCISE_WITH_NAME_ALREADY_EXISTS, IDS_MUST_BE_UNIQUE, NO_EXERCISE_FOUND
from ...models import ExerciseProgressRead, ExerciseRead
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

    async def progress(self, user_id: UUID | None, data: ExerciseProgress) -> list[ExerciseProgressRead]:
        results = json.loads(
            await self.client.query_json(
                """
                WITH
                    exercise_sets := (
                        SELECT ExerciseSet {
                            weight,
                            rep_count,
                        } FILTER .exercise.id = <uuid>$exercise_id
                    ),
                    groups := (
                        GROUP exercise_sets BY (.workout, .exercise)
                    )
                SELECT groups {
                    name := .key.exercise.name,
                    date := .key.workout.date,
                    avg_rep_count := math::mean(.elements.rep_count),
                    avg_weight := math::mean(.elements.weight),
                    max_weight := max(.elements.weight)
                }
                """,
                exercise_id=data.exercise_id,
            )
        )
        return [ExerciseProgressRead(**r) for r in results]
