from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from ...models import Exercise, ExerciseRead, Workout, WorkoutExerciseLink
from .base import BaseRepository
from .workouts import NO_WORKOUT_FOUND

NO_EXERCISE_FOUND = "No exercise found."


class ExerciseRepository(BaseRepository):
    def get_all(self, user_id: UUID | None, workout_id: UUID) -> list[ExerciseRead]:
        with Session(self.database) as session:
            workout = session.exec(
                select(Workout).where(Workout.id == workout_id).where(Workout.user_id == user_id)
            ).one_or_none()

            if not workout:
                raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

            return [ExerciseRead(**exercise.dict()) for exercise in workout.exercises]

    def detail(self, user_id: UUID | None, exercise_id: UUID) -> ExerciseRead:
        with Session(self.database) as session:
            exercise = (
                (
                    session.exec(
                        select(Exercise)
                        .join(WorkoutExerciseLink)
                        .join(Workout)
                        .where(Workout.user_id == user_id)
                        .where(Exercise.id == exercise_id)
                    )
                )
                .unique()
                .one_or_none()
            )

            if not exercise:
                raise HTTPException(status_code=404, detail=NO_EXERCISE_FOUND)

            return ExerciseRead(**exercise.dict())
