from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from swole_v2.models import Workout, WorkoutCreate, WorkoutRead, WorkoutUpdate

from ...exceptions import BusinessError
from ..validators import check_is_uuid
from .base import BaseRepository

NO_WORKOUT_FOUND = "No workout found."
NAME_AND_DATE_MUST_BE_UNIQUE = "Another workout already exists with the same name and date."


class WorkoutRepository(BaseRepository):
    def get_all(self, user_id: UUID | None) -> list[WorkoutRead]:
        with Session(self.database) as session:
            return [
                WorkoutRead(**result.dict()) for result in session.exec(select(Workout).where(Workout.user_id == user_id)).all()
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

    def delete(self, user_id: UUID | None, workout_id: str) -> None:
        workout_uuid = check_is_uuid(workout_id)
        with Session(self.database) as session:
            query = select(Workout).where(Workout.id == workout_uuid).where(Workout.user_id == user_id)
            workout = session.exec(query).one_or_none()

            if not workout:
                raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

            session.delete(workout)
            session.commit()

    def update(self, user_id: UUID | None, workout_id: str, update_data: WorkoutUpdate) -> WorkoutRead:
        workout_uuid = check_is_uuid(workout_id)
        with Session(self.database) as session:
            query = select(Workout).where(Workout.id == workout_uuid).where(Workout.user_id == user_id)
            workout = session.exec(query).one_or_none()

            if not workout:
                raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

            if update_data.name:
                workout.name = update_data.name
            if update_data.date:
                workout.date = update_data.date

            try:
                session.add(workout)
                session.commit()
                session.refresh(workout)

                return WorkoutRead(**workout.dict())
            except IntegrityError:
                raise BusinessError(NAME_AND_DATE_MUST_BE_UNIQUE)
