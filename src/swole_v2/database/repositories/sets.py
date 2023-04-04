from __future__ import annotations

import json
from typing import TYPE_CHECKING

from edgedb import MissingRequiredError
from fastapi import HTTPException

from ...errors.exceptions import BusinessError
from ...errors.messages import NO_SET_FOUND, SET_ADD_FAILED
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

    async def add(self, user_id: UUID | None, data: SetAdd) -> SetRead:
        try:
            result = await self.client.query_single_json(
                """
                WITH exercise_set := (
                    INSERT ExerciseSet {
                        weight := <int64>$weight,
                        rep_count := <int64>$rep_count,
                        workout := (
                            SELECT Workout
                            FILTER (.id = <uuid>$workout_id and .user.id = <uuid>$user_id)
                        ),
                        exercise := (
                            SELECT Exercise
                            FILTER (.id = <uuid>$exercise_id and .user.id = <uuid>$user_id)
                        )
                    }
                )
                SELECT exercise_set {id, weight, rep_count}
                """,
                weight=data.weight,
                rep_count=data.rep_count,
                workout_id=data.workout_id,
                exercise_id=data.exercise_id,
                user_id=user_id,
            )
            return SetRead.parse_raw(result)
        except MissingRequiredError as exc:
            raise BusinessError(SET_ADD_FAILED) from exc

    async def delete(self, user_id: UUID | None, data: SetDelete) -> None:
        result = json.loads(
            await self.client.query_single_json(
                """
                DELETE ExerciseSet
                FILTER .id = <uuid>$set_id
                """,
                set_id=data.set_id,
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
                    FILTER .id = <uuid>$set_id
                    SET {
                        weight := <optional int64>$weight ?? .weight,
                        rep_count := <optional int64>$rep_count ?? .rep_count
                    }
                )
                SELECT exercise_set {id, weight, rep_count}
                """,
                set_id=data.set_id,
                weight=data.weight,
                rep_count=data.rep_count,
            )
        )
        if result is None:
            raise HTTPException(status_code=404, detail=NO_SET_FOUND)
        return SetRead(**result)
