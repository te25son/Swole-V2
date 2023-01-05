from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ...errors.exceptions import BusinessError
from ...errors.messages import (
    EXERCISE_ALREADY_EXISTS_IN_WORKOUT,
    EXERCISE_WITH_NAME_ALREADY_EXISTS,
    NO_EXERCISE_FOUND,
    NO_WORKOUT_OR_EXERCISE_FOUND,
)
from ...models import Exercise, ExerciseRead, Workout
from ...schemas import (
    ExerciseAddToWorkout,
    ExerciseCreate,
    ExerciseDelete,
    ExerciseUpdate,
)
from .base import BaseRepository


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
            create_data = data.dict()
            create_data["user_id"] = user_id

            try:
                exercise = Exercise(**create_data)
                session.add(exercise)
                session.commit()
                session.refresh(exercise)

                return ExerciseRead(**exercise.dict())
            except IntegrityError:
                raise BusinessError(EXERCISE_WITH_NAME_ALREADY_EXISTS)

    def add_to_workout(self, user_id: UUID | None, data: ExerciseAddToWorkout) -> ExerciseRead:
        with Session(self.database) as session:
            result = session.exec(
                select(Exercise, Workout)
                .join(Workout, Workout.user_id == Exercise.user_id)
                .where(Workout.id == data.workout_id)
                .where(Exercise.id == data.exercise_id)
            ).all()

            if not result or len(result) > 1:
                raise HTTPException(status_code=404, detail=NO_WORKOUT_OR_EXERCISE_FOUND)

            exercise = result[0][0]
            workout = result[0][1]

            if exercise in workout.exercises:
                raise BusinessError(EXERCISE_ALREADY_EXISTS_IN_WORKOUT)

            workout.exercises.append(exercise)
            session.add(workout)
            session.commit()
            session.refresh(exercise)

            return ExerciseRead(**exercise.dict())

    def update(self, user_id: UUID | None, data: ExerciseUpdate) -> ExerciseRead:
        with Session(self.database) as session:
            exercise = session.exec(
                select(Exercise).where(Exercise.user_id == user_id).where(Exercise.id == data.exercise_id)
            ).one_or_none()

            if not exercise:
                raise HTTPException(status_code=404, detail=NO_EXERCISE_FOUND)

            exercise.name = data.name

            try:
                session.add(exercise)
                session.commit()
                session.refresh(exercise)
                return ExerciseRead(**exercise.dict())
            except IntegrityError:
                raise BusinessError(EXERCISE_WITH_NAME_ALREADY_EXISTS)

    def delete(self, user_id: UUID | None, data: ExerciseDelete) -> None:
        with Session(self.database) as session:
            exercise = session.exec(
                select(Exercise).where(Exercise.user_id == user_id).where(Exercise.id == data.exercise_id)
            ).one_or_none()

            if not exercise:
                raise HTTPException(status_code=404, detail=NO_EXERCISE_FOUND)

            session.delete(exercise)
            session.commit()
