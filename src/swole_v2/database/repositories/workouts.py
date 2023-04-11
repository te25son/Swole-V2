from __future__ import annotations

import json
from typing import TYPE_CHECKING

from edgedb import CardinalityViolationError, ConstraintViolationError
from fastapi import HTTPException

from ...errors.exceptions import BusinessError
from ...errors.messages import NAME_AND_DATE_MUST_BE_UNIQUE, NO_EXERCISE_FOUND, NO_WORKOUT_FOUND
from ...models import ExerciseRead, Workout, WorkoutRead
from .base import BaseRepository

if TYPE_CHECKING:
    from uuid import UUID

    from ...schemas import WorkoutAddExercise, WorkoutCopy, WorkoutCreate, WorkoutGetAllExercises, WorkoutUpdate


class WorkoutRepository(BaseRepository):
    async def get_all(self, user_id: UUID | None) -> list[WorkoutRead]:
        results = json.loads(
            await self.client.query_json(
                """
                SELECT Workout {id, name, date}
                FILTER .user.id = <uuid>$user_id
                ORDER BY .date DESC
                """,
                user_id=user_id,
            )
        )
        return [WorkoutRead(**result) for result in results]

    async def add_exercises(self, user_id: UUID | None, data: list[WorkoutAddExercise]) -> list[WorkoutRead]:
        try:
            workouts = await self.query_json(
                """
                WITH workouts := (
                    FOR data IN array_unpack(<array<json>>$data) UNION (
                        UPDATE Workout
                        FILTER (.id = <uuid>data['workout_id'] AND .user.id = <uuid>$user_id)
                        SET {
                            exercises += assert_exists((
                                SELECT Exercise
                                FILTER .id = <uuid>data['exercise_id'] AND .user.id = <uuid>$user_id
                            ))
                        }
                    )
                )
                SELECT workouts {id, name, date}
                """,
                # Convert from set to list to ensure unique values
                data=list({d.json() for d in data}),
                user_id=user_id,
            )
            return [WorkoutRead(**workout) for workout in workouts]
        except CardinalityViolationError as error:
            raise BusinessError(NO_EXERCISE_FOUND) from error

    async def get_all_exercises(self, user_id: UUID | None, data: WorkoutGetAllExercises) -> list[ExerciseRead]:
        result = json.loads(
            await self.client.query_single_json(
                """
                SELECT Workout {name, date, exercises: {id, name, notes}}
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
                SELECT Workout {id, name, date}
                FILTER (.id = <uuid>$workout_id and .user.id = <uuid>$user_id)
                """,
                workout_id=workout_id,
                user_id=user_id,
            )
        )

        if result is None:
            raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

        return WorkoutRead(**result)

    async def create(self, user_id: UUID | None, data: list[WorkoutCreate]) -> list[WorkoutRead]:
        try:
            workouts = await self.query_json(
                """
                WITH workouts := (
                    FOR workout IN array_unpack(<array<json>>$data) UNION (
                        INSERT Workout {
                            name := <str>workout['name'],
                            date := <cal::local_date>workout['date'],
                            user := (
                                SELECT User
                                FILTER .id = <uuid>$user_id
                            )
                        }
                    )
                )
                SELECT workouts {id, name, date}
                """,
                data=[d.json() for d in data],
                user_id=user_id,
            )
            return [WorkoutRead(**workout) for workout in workouts]
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
                    SELECT workout {id, name, date}
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

    async def copy(self, user_id: UUID | None, data: WorkoutCopy) -> WorkoutRead:
        try:
            workout = await self.client.query_single_json(
                """
                WITH
                    existing_workout := assert_exists(
                        (SELECT Workout FILTER (.id = <uuid>$workout_id and .user.id = <uuid>$user_id))
                    ),
                    copied_workout := (
                        INSERT Workout {
                            name := existing_workout.name,
                            date := <cal::local_date>$date,
                            user := existing_workout.user,
                            exercises := existing_workout.exercises
                        }
                    )
                SELECT copied_workout {id, name, date}
                """,
                workout_id=data.workout_id,
                user_id=user_id,
                date=data.date,
            )
            return WorkoutRead.parse_raw(workout)
        except CardinalityViolationError as exc:
            raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND) from exc
        except ConstraintViolationError as exc:
            raise BusinessError(NAME_AND_DATE_MUST_BE_UNIQUE) from exc
