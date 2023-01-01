from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from swole_v2.models import Workout, WorkoutCreate, WorkoutRead, WorkoutUpdate

from ...exceptions import BusinessError
from .base import BaseRepository

WORKOUT_WITH_ID_NOT_FOUND = "No workout found with given id."
NAME_AND_DATE_MUST_BE_UNIQUE = "Workout name and date must be unique."


class WorkoutRepository(BaseRepository):
    def get_all(self, user_id: UUID | None) -> list[WorkoutRead]:
        with Session(self.database) as session:
            return [
                WorkoutRead(**result.dict())
                for result in session.exec(select(Workout).where(Workout.user_id == user_id)).all()
            ]

    def create(self, user_id: UUID | None, create_data: WorkoutCreate) -> WorkoutRead:
        with Session(self.database) as session:
            data = create_data.dict()
            data["user_id"] = user_id

            try:
                session.add(created_workout := Workout(**data))
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
                raise BusinessError(WORKOUT_WITH_ID_NOT_FOUND)

            session.delete(workout)
            session.commit()

    def update(self, user_id: UUID | None, workout_id: UUID, update_data: WorkoutUpdate) -> WorkoutRead:
        with Session(self.database) as session:
            query = select(Workout).where(Workout.id == workout_id).where(Workout.user_id == user_id)
            workout = session.exec(query).one_or_none()

            if not workout:
                raise BusinessError(WORKOUT_WITH_ID_NOT_FOUND)

            if update_data.name:
                workout.name = update_data.name
            if update_data.date:
                workout.date = update_data.date

            session.add(workout)
            session.commit()
            session.refresh(workout)

            return WorkoutRead(**workout.dict())
