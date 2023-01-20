import json
from uuid import UUID

from edgedb import ConstraintViolationError
from fastapi import HTTPException

from ...errors.exceptions import BusinessError
from ...errors.messages import (
    EXERCISE_WITH_NAME_ALREADY_EXISTS,
    NO_EXERCISE_FOUND,
)
from ...models import ExerciseRead
from ...schemas import (
    ExerciseAddToWorkout,
    ExerciseCreate,
    ExerciseDelete,
    ExerciseUpdate,
)
from .base import BaseRepository


class ExerciseRepository(BaseRepository):
    async def get_all(self, user_id: UUID | None) -> list[ExerciseRead]:
        results = json.loads(
            await self.client.query_json(
                """
                SELECT Exercise {name, notes}
                FILTER .user.id = <uuid>$user_id
                """,
                user_id=user_id,
            )
        )
        return [ExerciseRead(**result) for result in results]

    async def detail(self, user_id: UUID | None, exercise_id: UUID) -> ExerciseRead:
        result = json.loads(
            await self.client.query_single_json(
                """
                SELECT Exercise {name, notes}
                FILTER (.id = <uuid>$exercise_id and .user.id = <uuid>$user_id)
                """,
                exercise_id=exercise_id,
                user_id=user_id,
            )
        )

        if result is None:
            raise HTTPException(status_code=404, detail=NO_EXERCISE_FOUND)

        return ExerciseRead(**result)

    async def create(self, user_id: UUID | None, data: ExerciseCreate) -> ExerciseRead:
        try:
            exercise = await self.client.query_single_json(
                """
                WITH exercise := (
                    INSERT Exercise {
                        name := <str>$name,
                        notes := <optional str>$notes,
                        user := (SELECT User FILTER .id = <uuid>$user_id)
                    }
                )
                SELECT exercise {name, notes}
                """,
                name=data.name,
                notes=data.notes,
                user_id=user_id,
            )
            return ExerciseRead.parse_raw(exercise)
        except ConstraintViolationError:
            raise BusinessError(EXERCISE_WITH_NAME_ALREADY_EXISTS)

    async def add_to_workout(self, user_id: UUID | None, data: ExerciseAddToWorkout) -> ExerciseRead:
        result = json.loads(
            await self.client.query_single_json(
                """
                WITH exercise := (
                    UPDATE Exercise
                    FILTER (.id = <uuid>$exercise_id and .user.id = <uuid>$user_id)
                    SET {
                        workouts += (SELECT Workout FILTER .id = <uuid>$workout_id)
                    }
                )
                SELECT exercise {name, notes}
                """,
                workout_id=data.workout_id,
                exercise_id=data.exercise_id,
                user_id=user_id,
            )
        )

        if result is None:
            raise HTTPException(status_code=404, detail=NO_EXERCISE_FOUND)

        return ExerciseRead(**result)

    async def update(self, user_id: UUID | None, data: ExerciseUpdate) -> ExerciseRead:
        try:
            result = await self.client.query_single_json(
                """
                WITH exercise := (
                    UPDATE Exercise
                    FILTER (.id = <uuid>$exercise_id and .user.id = <uuid>$user_id)
                    SET {
                        name := <optional str>$name ?? .name,
                        notes := <optional str>$notes ?? .notes
                    }
                )
                SELECT exercise {name, notes}
                """,
                exercise_id=data.exercise_id,
                user_id=user_id,
                name=data.name,
                notes=data.notes,
            )
            return ExerciseRead.parse_raw(result)
        except ConstraintViolationError:
            raise BusinessError(EXERCISE_WITH_NAME_ALREADY_EXISTS)

    async def delete(self, user_id: UUID | None, data: ExerciseDelete) -> None:
        await self.client.query_single_json(
            """
            DELETE Exercise
            FILTER (.id = <uuid>$exercise_id and .user.id = <uuid>$user_id)
            """,
            exercise_id=data.exercise_id,
            user_id=user_id,
        )
