from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ...errors.exceptions import BusinessError
from ...errors.messages import NAME_AND_DATE_MUST_BE_UNIQUE, NO_WORKOUT_FOUND
from ...models import ExerciseRead, Workout, WorkoutRead
from ...schemas import WorkoutCreate, WorkoutGetAllExercises, WorkoutUpdate
from .base import BaseRepository


class WorkoutRepository(BaseRepository):
    def get_all(self, user_id: UUID | None) -> list[WorkoutRead]:
        with Session(self.database) as session:
            return [
                WorkoutRead(**result.dict())
                for result in session.exec(select(Workout).where(Workout.user_id == user_id)).all()
            ]

    def get_all_exercises(self, user_id: UUID | None, data: WorkoutGetAllExercises) -> list[ExerciseRead]:
        with Session(self.database) as session:
            workout = session.exec(
                select(Workout).where(Workout.id == data.workout_id).where(Workout.user_id == user_id)
            ).one_or_none()

            if not workout:
                raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

            return [ExerciseRead(**link.exercise.dict()) for link in workout.exercise_links]

    def detail(self, user_id: UUID | None, workout_id: UUID) -> WorkoutRead:
        with Session(self.database) as session:
            query = select(Workout).where(Workout.id == workout_id).where(Workout.user_id == user_id)
            workout = session.exec(query).one_or_none()

            if not workout:
                raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

            return WorkoutRead(**workout.dict())

    def create(self, user_id: UUID | None, data: WorkoutCreate) -> WorkoutRead:
        with Session(self.database) as session:
            create_data = data.dict()
            create_data["user_id"] = user_id

            try:
                session.add(created_workout := Workout(**create_data))
                session.commit()
                session.refresh(created_workout)

                return WorkoutRead(**created_workout.dict())
            except IntegrityError:
                raise BusinessError(NAME_AND_DATE_MUST_BE_UNIQUE)

    def delete(self, user_id: UUID | None, workout_id: UUID) -> None:
        with Session(self.database) as session:
            query = select(Workout).where(Workout.id == workout_id).where(Workout.user_id == user_id)
            workout = session.exec(query).one_or_none()

            if not workout:
                raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

            session.delete(workout)
            session.commit()

    def update(self, user_id: UUID | None, data: WorkoutUpdate) -> WorkoutRead:
        with Session(self.database) as session:
            query = select(Workout).where(Workout.id == data.workout_id).where(Workout.user_id == user_id)
            workout = session.exec(query).one_or_none()

            if not workout:
                raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

            workout.name = data.name or workout.name
            workout.date = data.date or workout.date

            try:
                session.add(workout)
                session.commit()
                session.refresh(workout)

                return WorkoutRead(**workout.dict())
            except IntegrityError:
                raise BusinessError(NAME_AND_DATE_MUST_BE_UNIQUE)
