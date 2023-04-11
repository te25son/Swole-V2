from __future__ import annotations

import json
from typing import TYPE_CHECKING

from edgedb import CardinalityViolationError, ConstraintViolationError
from fastapi import HTTPException

from ...errors.exceptions import BusinessError
from ...errors.messages import NAME_AND_DATE_MUST_BE_UNIQUE, NO_EXERCISE_FOUND, NO_WORKOUT_FOUND
from ...models import Workout, WorkoutRead
from .base import BaseRepository

if TYPE_CHECKING:
    from uuid import UUID

    from ...schemas import WorkoutAddExercise, WorkoutCopy, WorkoutCreate, WorkoutDelete, WorkoutDetail, WorkoutUpdate


class WorkoutRepository(BaseRepository):
    async def get_all(self, user_id: UUID | None) -> list[WorkoutRead]:
        results = await self.query_json(
            """
            SELECT Workout {id, name, date}
            FILTER .user.id = <uuid>$user_id
            ORDER BY .date DESC
            """,
            user_id=user_id,
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
                data=data,
                user_id=user_id,
            )
            return [WorkoutRead(**workout) for workout in workouts]
        except CardinalityViolationError as error:
            raise BusinessError(NO_EXERCISE_FOUND) from error

    async def detail(
        self, user_id: UUID | None, data: list[WorkoutDetail], with_exercises: bool
    ) -> list[WorkoutRead | Workout]:
        try:
            select_query = "{id, name, date, exercises: {id, name, notes}}" if with_exercises else "{id, name, date}"
            workouts = await self.query_json(
                f"""
                WITH workouts := (
                    FOR data IN array_unpack(<array<json>>$data) UNION assert_exists((
                        SELECT Workout
                        FILTER .id = <uuid>data['workout_id'] AND .user.id = <uuid>$user_id
                    ))
                )
                SELECT workouts {select_query}
                ORDER BY .date DESC
                """,
                data=data,
                user_id=user_id,
            )
            return [Workout(**workout) if with_exercises else WorkoutRead(**workout) for workout in workouts]
        except CardinalityViolationError as error:
            raise BusinessError(NO_WORKOUT_FOUND) from error

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
                data=data,
                user_id=user_id,
            )
            return [WorkoutRead(**workout) for workout in workouts]
        except ConstraintViolationError as exc:
            raise BusinessError(NAME_AND_DATE_MUST_BE_UNIQUE) from exc

    async def delete(self, user_id: UUID | None, data: list[WorkoutDelete]) -> None:
        try:
            await self.query_json(
                """
                WITH workouts := (
                    FOR data IN array_unpack(<array<json>>$data) UNION assert_exists((
                        SELECT Workout
                        FILTER .id = <uuid>data['workout_id'] AND .user.id = <uuid>$user_id
                    ))
                )
                DELETE workouts
                """,
                data=data,
                user_id=user_id,
            )
        except CardinalityViolationError as error:
            raise BusinessError(NO_WORKOUT_FOUND) from error

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
