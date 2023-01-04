from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from ...models import Exercise, ExerciseRead, Workout, WorkoutExerciseLink, ExerciseCreate
from .base import BaseRepository
from .workouts import NO_WORKOUT_FOUND
from ...exceptions import BusinessError

NO_EXERCISE_FOUND = "No exercise found."
NAME_MUST_BE_UNIQUE = "Name must be unique"


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

    def create(self, user_id: UUID | None, data: ExerciseCreate) -> ExerciseRead:
        with Session(self.database) as session:
            workout = session.exec(
                select(Workout).where(Workout.id == data.workout_id).where(Workout.user_id == user_id)
            ).one_or_none()

            if not workout:
                raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

            try:
                workout.exercieses.append(created_exercise := Exercise(**data.dict()))
                session.add(workout)
                session.commit()
                session.refresh(created_exercise)

                return ExerciseRead(**created_exercise.dict())
            except IntegrityError:
                raise BusinessError(NAME_MUST_BE_UNIQUE)
