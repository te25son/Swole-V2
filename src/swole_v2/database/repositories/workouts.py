import json
from uuid import UUID

from edgedb import ConstraintViolationError
from fastapi import HTTPException

from ...errors.exceptions import BusinessError
from ...errors.messages import NAME_AND_DATE_MUST_BE_UNIQUE, NO_WORKOUT_FOUND
from ...models import ExerciseRead, Workout, WorkoutRead
from ...schemas import WorkoutAddExercise, WorkoutCreate, WorkoutGetAllExercises, WorkoutUpdate
from .base import BaseRepository


class WorkoutRepository(BaseRepository):
    async def get_all(self, user_id: UUID | None) -> list[WorkoutRead]:
        results = json.loads(
            await self.client.query_json(
                """
                SELECT Workout {name, date}
                FILTER .user.id = <uuid>$user_id
                """,
                user_id=user_id,
            )
        )
        return [WorkoutRead(**result) for result in results]

    async def add_exercise(self, user_id: UUID | None, data: WorkoutAddExercise) -> WorkoutRead:
        result = json.loads(
            await self.client.query_single_json(
                """
                WITH workout := (
                    UPDATE Workout
                    FILTER (.id = <uuid>$workout_id and .user.id = <uuid>$user_id)
                    SET {
                        exercises += (SELECT Exercise FILTER .id = <uuid>$exercise_id)
                    }
                )
                SELECT workout {name, date}
                """,
                workout_id=data.workout_id,
                exercise_id=data.exercise_id,
                user_id=user_id,
            )
        )

        if result is None:
            raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

        return WorkoutRead(**result)

    async def get_all_exercises(self, user_id: UUID | None, data: WorkoutGetAllExercises) -> list[ExerciseRead]:
        result = json.loads(
            await self.client.query_single_json(
                """
                SELECT Workout {name, date, exercises: {name, notes}}
                FILTER (.id = <uuid>$workout_id and .user.id = <uuid>$user_id)
                """,
                workout_id=data.workout_id,
                user_id=user_id,
            )
        )

        if result is None:
            raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

        return [ExerciseRead(**e.dict()) for e in Workout(**result).exercises]

    async def detail(self, user_id: UUID | None, workout_id: UUID) -> WorkoutRead:
        result = json.loads(
            await self.client.query_single_json(
                """
                SELECT Workout {name, date}
                FILTER (.id = <uuid>$workout_id and .user.id = <uuid>$user_id)
                """,
                workout_id=workout_id,
                user_id=user_id,
            )
        )

        if result is None:
            raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

        return WorkoutRead(**result)

    async def create(self, user_id: UUID | None, data: WorkoutCreate) -> WorkoutRead:
        try:
            workout = await self.client.query_single_json(
                """
                WITH workout := (
                    INSERT Workout {
                        name := <str>$name,
                        date := <cal::local_date>$date,
                        user := (
                            SELECT User
                            FILTER .id = <uuid>$user_id
                        )
                    }
                )
                SELECT workout {name, date}
                """,
                name=data.name,
                date=data.date,
                user_id=user_id,
            )
            return WorkoutRead.parse_raw(workout)
        except ConstraintViolationError as exc:
            raise BusinessError(NAME_AND_DATE_MUST_BE_UNIQUE) from exc

    async def delete(self, user_id: UUID | None, workout_id: UUID) -> None:
        result = json.loads(
            await self.client.query_single_json(
                """
                DELETE Workout
                FILTER (.id = <uuid>$workout_id and .user.id = <uuid>$user_id)
                """,
                workout_id=workout_id,
                user_id=user_id,
            )
        )
        if result is None:
            raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

    async def update(self, user_id: UUID | None, data: WorkoutUpdate) -> WorkoutRead:
        try:
            result = json.loads(
                await self.client.query_single_json(
                    """
                    WITH workout := (
                        UPDATE Workout
                        FILTER (.id = <uuid>$workout_id and .user.id = <uuid>$user_id)
                        SET {
                            name := <optional str>$name ?? .name,
                            date := <optional cal::local_date>$date ?? .date
                        }
                    )
                    SELECT workout {name, date}
                    """,
                    workout_id=data.workout_id,
                    user_id=user_id,
                    name=data.name,
                    date=data.date,
                )
            )
            if result is None:
                raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)
            return WorkoutRead(**result)
        except ConstraintViolationError as exc:
            raise BusinessError(NAME_AND_DATE_MUST_BE_UNIQUE) from exc
