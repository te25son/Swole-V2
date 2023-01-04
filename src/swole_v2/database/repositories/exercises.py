from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ...exceptions import BusinessError
from ...models import Exercise, ExerciseCreate, ExerciseRead, Workout
from .base import BaseRepository
from .workouts import NO_WORKOUT_FOUND

NO_EXERCISE_FOUND = "No exercise found."
EXERCISE_ALREADY_EXISTS_IN_WORKOUT = "Exercise with the given name already exists in this workout."


class ExerciseRepository(BaseRepository):
    def get_all(self, user_id: UUID | None) -> list[ExerciseRead]:
        with Session(self.database) as session:
            return [
                ExerciseRead(**e.dict())
                for e in session.exec(select(Exercise).where(Exercise.user_id == user_id)).all()
            ]

    def detail(self, user_id: UUID | None, exercise_id: UUID) -> ExerciseRead:
        with Session(self.database) as session:
            exercise = (
                session.exec(select(Exercise).where(Exercise.user_id == user_id).where(Exercise.id == exercise_id))
            ).one_or_none()

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

            create_data = data.dict()
            create_data["user_id"] = user_id

            try:
                workout.exercises.append(created_exercise := Exercise(**create_data))
                session.add(workout)
                session.commit()
                session.refresh(created_exercise)

                return ExerciseRead(**created_exercise.dict())
            except IntegrityError:
                raise BusinessError(EXERCISE_ALREADY_EXISTS_IN_WORKOUT)
