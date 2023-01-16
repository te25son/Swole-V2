import json
from uuid import UUID

from edgedb import ConstraintViolationError
from fastapi import HTTPException

from ...errors.exceptions import BusinessError
from ...errors.messages import NAME_AND_DATE_MUST_BE_UNIQUE, NO_WORKOUT_FOUND
from ...models import ExerciseRead, Workout, WorkoutRead
from ...schemas import WorkoutCreate, WorkoutGetAllExercises, WorkoutUpdate
from .base import BaseRepository


class WorkoutRepository(BaseRepository):
    def get_all(self, user_id: UUID | None) -> list[WorkoutRead]:
        results = json.loads(
            self.client.query_json("SELECT Workout {name, date} FILTER .user.id = <uuid>$user_id", user_id=user_id)
        )
        return [WorkoutRead(**result) for result in results]

    def get_all_exercises(self, user_id: UUID | None, data: WorkoutGetAllExercises) -> list[ExerciseRead]:
        result = json.loads(
            self.client.query_single_json(
                "SELECT Workout {exercises: {name}} FILTER (.id = <uuid>$workout_id and .user.id = <uuid>$user_id)",
                workout_id=data.workout_id,
                user_id=user_id,
            )
        )

        if result is None:
            raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

        return Workout(**result).exercises or []

    def detail(self, user_id: UUID | None, workout_id: UUID) -> WorkoutRead:
        result = json.loads(
            self.client.query_single_json(
                "SELECT Workout {name, date} FILTER (.id = <uuid>$workout_id and .user.id = <uuid>$user_id)",
                workout_id=workout_id,
                user_id=user_id,
            )
        )

        if result is None:
            raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

        return WorkoutRead(**result)

    def create(self, user_id: UUID | None, data: WorkoutCreate) -> WorkoutRead:
        try:
            result = json.loads(
                self.client.query_single_json(
                    """
                INSERT Workout {
                    name := <str>$name,
                    date := <cal::local_date>$date,
                    user := (SELECT User FILTER .id = <uuid>$user_id)
                }""",
                    name=data.name,
                    date=data.date,
                    user_id=user_id,
                )
            )
            workout = self.client.query_single_json(
                "SELECT Workout {name, date} FILTER .id = <uuid>$workout_id", workout_id=result["id"]
            )
            return WorkoutRead.parse_raw(workout)
        except ConstraintViolationError:
            raise BusinessError(NAME_AND_DATE_MUST_BE_UNIQUE)

    def delete(self, user_id: UUID | None, workout_id: UUID) -> None:
        self.client.query_single_json(
            "DELETE Workout FILTER (.id = <uuid>$workout_id and .user.id = <uuid>$user_id)",
            workout_id=workout_id,
            user_id=user_id,
        )

    def update(self, user_id: UUID | None, data: WorkoutUpdate) -> WorkoutRead:
        try:
            self.client.query_single_json(
                """
                UPDATE Workout
                FILTER (.id = <uuid>$workout_id and .user.id = <uuid>$user_id)
                SET {
                    name := <optional str>$name ?? .name,
                    date := <optional cal::local_date>$date ?? .date
                }""",
                workout_id=data.workout_id,
                user_id=user_id,
                name=data.name,
                date=data.date,
            )
            result = self.client.query_single_json(
                "SELECT Workout {name, date} FILTER .id = <uuid>$workout_id", workout_id=data.workout_id
            )
            return WorkoutRead.parse_raw(result)
        except ConstraintViolationError:
            raise BusinessError(NAME_AND_DATE_MUST_BE_UNIQUE)
