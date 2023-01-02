from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from ...models import ExerciseRead, Workout
from .base import BaseRepository
from .workouts import NO_WORKOUT_FOUND


class ExerciseRepository(BaseRepository):
    def get_all(self, user_id: UUID | None, workout_id: UUID) -> list[ExerciseRead]:
        with Session(self.database) as session:
            workout = session.exec(
                select(Workout).where(Workout.id == workout_id).where(Workout.user_id == user_id)
            ).one_or_none()

            if not workout:
                raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

            return [ExerciseRead(**exercise.dict()) for exercise in workout.exercises]
