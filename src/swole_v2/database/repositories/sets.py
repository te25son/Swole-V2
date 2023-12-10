from __future__ import annotations

import json
from typing import TYPE_CHECKING

from edgedb import CardinalityViolationError
from fastapi import HTTPException

from ...errors.exceptions import BusinessError
from ...errors.messages import NO_EXERCISE_FOUND, NO_SET_FOUND, NO_WORKOUT_FOUND
from ...models import SetRead
from .base import BaseRepository

if TYPE_CHECKING:
    from uuid import UUID

    from ...schemas import SetAdd, SetDelete, SetGetAll, SetUpdate


class SetRepository(BaseRepository):
    async def get_all(self, user_id: UUID | None, data: SetGetAll) -> list[SetRead]:
        results = json.loads(
            await self.client.query_json(
                """
                SELECT ExerciseSet {id, weight, rep_count}
                FILTER (
                    .exercise.id = <uuid>$exercise_id
                    and .workout.id = <uuid>$workout_id
                    and .exercise.user.id = <uuid>$user_id
                    and .workout.user.id = <uuid>$user_id
                )
                """,
                workout_id=data.workout_id,
                exercise_id=data.exercise_id,
                user_id=user_id,
            )
        )

        return [SetRead(**result) for result in results]

    async def add(self, user_id: UUID | None, data: list[SetAdd]) -> list[SetRead]:
        try:
            exercise_sets = await self.query_owned_json(
                f"""
                WITH exercise_sets := (
                    FOR data IN array_unpack(<array<json>>$data) UNION (
                        INSERT ExerciseSet {{
                            weight := <int64>data['weight'],
                            rep_count := <int64>data['rep_count'],
                            workout := (
                                SELECT assert_exists((
                                    SELECT Workout
                                    FILTER .id = <uuid>data['workout_id'] AND .user.id = <uuid>$user_id
                                ), message := '{NO_WORKOUT_FOUND}')
                            ),
                            exercise := (
                                SELECT assert_exists((
                                    SELECT Exercise
                                    FILTER .id = <uuid>data['exercise_id'] AND .user.id = <uuid>$user_id
                                ), message := '{NO_EXERCISE_FOUND}')
                            )
                        }}
                    )
                )
                SELECT exercise_sets {{id, weight, rep_count}}
                """,
                data=data,
                user_id=user_id,
                unique=False,
            )
            return [SetRead(**exercise_set) for exercise_set in exercise_sets]
        except CardinalityViolationError as error:
            raise BusinessError(error.args[0]) from error

    async def delete(self, user_id: UUID | None, data: SetDelete) -> None:
        result = json.loads(
            await self.client.query_single_json(
                """
                DELETE ExerciseSet
                FILTER (
                    .id = <uuid>$set_id
                    and .exercise.user.id = <uuid>$user_id
                    and .workout.user.id = <uuid>$user_id
                )
                """,
                set_id=data.set_id,
                user_id=user_id,
            )
        )
        if result is None:
            raise HTTPException(status_code=404, detail=NO_SET_FOUND)

    async def update(self, user_id: UUID | None, data: SetUpdate) -> SetRead:
        result = json.loads(
            await self.client.query_single_json(
                """
                WITH exercise_set := (
                    UPDATE ExerciseSet
                    FILTER (
                        .id = <uuid>$set_id
                        and .exercise.user.id = <uuid>$user_id
                        and .workout.user.id = <uuid>$user_id
                    )
                    SET {
                        weight := <optional int64>$weight ?? .weight,
                        rep_count := <optional int64>$rep_count ?? .rep_count
                    }
                )
                SELECT exercise_set {id, weight, rep_count}
                """,
                set_id=data.set_id,
                user_id=user_id,
                weight=data.weight,
                rep_count=data.rep_count,
            )
        )
        if result is None:
            raise HTTPException(status_code=404, detail=NO_SET_FOUND)
        return SetRead(**result)
