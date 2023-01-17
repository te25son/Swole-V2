import json
from uuid import UUID

from edgedb import MissingRequiredError

from ...errors.exceptions import BusinessError
from ...errors.messages import SET_ADD_FAILED
from ...models import SetRead
from ...schemas import SetAdd, SetDelete, SetGetAll, SetUpdate
from .base import BaseRepository


class SetRepository(BaseRepository):
    async def get_all(self, user_id: UUID | None, data: SetGetAll) -> list[SetRead]:
        results = json.loads(
            await self.client.query_json(
                """
                SELECT ExerciseSet {weight, rep_count}
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
                            FILTER .id = <uuid>$workout_id and .user.id = <uuid>$user_id
                        ),
                        exercise := (
                            SELECT Exercise
                            FILTER .id = <uuid>$exercise_id and .user.id = <uuid>$user_id
                        ),
                    }
                )
                SELECT exercise_set {weight, rep_count}
                """,
                weight=data.weight,
                rep_count=data.rep_count,
                workout_id=data.workout_id,
                exercise_id=data.exercise_id,
                user_id=user_id,
            )
            return SetRead.parse_raw(result)
        except MissingRequiredError:
            raise BusinessError(SET_ADD_FAILED)

    async def delete(self, user_id: UUID | None, data: SetDelete) -> None:
        await self.client.query_single_json(
            """
            DELETE ExerciseSet
            FILTER .id = <uuid>$set_id
            """,
            set_id=data.set_id,
        )

    async def update(self, user_id: UUID | None, data: SetUpdate) -> SetRead:
        result = await self.client.query_single_json(
            """
            WITH exercise_set := (
                UPDATE ExerciseSet
                FILTER .id = <uuid>$set_id
                SET {
                    weight := <optional int64>$weight ?? .weight,
                    rep_count := <optional int64>$rep_count ?? .rep_count
                }
            )
            SELECT exercise_set {weight, rep_count}
            """,
            set_id=data.set_id,
            weight=data.weight,
            rep_count=data.rep_count,
        )
        return SetRead.parse_raw(result)
