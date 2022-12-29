from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from swole_v2.models import (
    Result,
    Workout,
    WorkoutCreate,
    WorkoutRead,
    WorkoutUpdate,
)

from .base import BaseRepository

WORKOUT_WITH_ID_NOT_FOUND = "No workout found with given id."
NAME_AND_DATE_MUST_BE_UNIQUE = "Workout name and date must be unique."


class WorkoutRepository(BaseRepository):
    def get_all(self, user_id: UUID | None) -> Result:
        with Session(self.database) as session:
            results = session.exec(select(Workout).where(Workout.user_id == user_id)).all()
            return Result(success=True, product=[WorkoutRead(**r.dict()) for r in results])

    def create(self, user_id: UUID | None, create_data: WorkoutCreate) -> Result:
        with Session(self.database) as session:
            data = create_data.dict()
            data["user_id"] = user_id

            try:
                session.add(created_workout := Workout(**data))
                session.commit()
                session.refresh(created_workout)

                return Result(success=True, product=[WorkoutRead(**created_workout.dict())])
            except IntegrityError:
                return Result(success=False, message=NAME_AND_DATE_MUST_BE_UNIQUE)

    def delete(self, user_id: UUID | None, workout_id: UUID) -> Result:
        with Session(self.database) as session:
            query = select(Workout).where(Workout.id == workout_id).where(Workout.user_id == user_id)
            workout = session.exec(query).one_or_none()

            if workout:
                session.delete(workout)
                session.commit()

                return Result(success=True)
            return Result(success=False, message=WORKOUT_WITH_ID_NOT_FOUND.format(workout_id))

    def update(self, user_id: UUID | None, workout_id: UUID, update_data: WorkoutUpdate) -> Result:
        with Session(self.database) as session:
            query = select(Workout).where(Workout.id == workout_id).where(Workout.user_id == user_id)
            workout = session.exec(query).one_or_none()

            if workout:
                if update_data.name:
                    workout.name = update_data.name
                if update_data.date:
                    workout.date = update_data.date
                session.add(workout)
                session.commit()
                session.refresh(workout)

                return Result(success=True, product=[WorkoutRead(**workout.dict())])
            return Result(success=False, message=WORKOUT_WITH_ID_NOT_FOUND)
