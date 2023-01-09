from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_
from sqlmodel import Session, select

from ...errors.messages import (
    NO_EXERCISE_FOUND,
    NO_SET_FOUND,
    NO_WORKOUT_FOUND,
)
from ...models import Exercise, Set, SetRead, Workout
from ...schemas import SetAdd, SetDelete, SetGetAll, SetUpdate
from .base import BaseRepository


class SetRepository(BaseRepository):
    def get_all(self, user_id: UUID | None, data: SetGetAll) -> list[SetRead]:
        with Session(self.database) as session:
            sets = session.exec(
                select(Set)
                .where(and_(Set.exercise_id == data.exercise_id, Set.exercise_user_id == user_id))
                .where(and_(Set.workout_id == data.workout_id, Set.workout_user_id == user_id))
            ).all()

            return [SetRead(**s.dict()) for s in sets]

    def add(self, user_id: UUID | None, data: SetAdd) -> SetRead:
        with Session(self.database) as session:
            exercise = session.exec(
                select(Exercise).where(Exercise.id == data.exercise_id).where(Exercise.user_id == user_id)
            ).one_or_none()
            workout = session.exec(
                select(Workout).where(Workout.id == data.workout_id).where(Workout.user_id == user_id)
            ).one_or_none()

            if not exercise:
                raise HTTPException(status_code=404, detail=NO_EXERCISE_FOUND)
            if not workout:
                raise HTTPException(status_code=404, detail=NO_WORKOUT_FOUND)

            set = Set(rep_count=data.rep_count, weight=data.weight, workout=workout, exercise=exercise)
            session.add(set)
            session.commit()
            session.refresh(set)

            return SetRead(**set.dict())

    def delete(self, user_id: UUID | None, data: SetDelete) -> None:
        with Session(self.database) as session:
            set = session.exec(
                select(Set)
                .where(Set.id == data.set_id)
                .where(and_(Set.exercise_id == data.exercise_id, Set.exercise_user_id == user_id))
                .where(and_(Set.workout_id == data.workout_id, Set.workout_user_id == user_id))
            ).one_or_none()

            if not set:
                raise HTTPException(status_code=404, detail=NO_SET_FOUND)

            session.delete(set)
            session.commit()

    def update(self, user_id: UUID | None, data: SetUpdate) -> SetRead:
        with Session(self.database) as session:
            set = session.exec(
                select(Set)
                .where(Set.id == data.set_id)
                .where(and_(Set.exercise_id == data.exercise_id, Set.exercise_user_id == user_id))
                .where(and_(Set.workout_id == data.workout_id, Set.workout_user_id == user_id))
            ).one_or_none()

            if not set:
                raise HTTPException(status_code=404, detail=NO_SET_FOUND)

            set.rep_count = data.rep_count or set.rep_count
            set.weight = data.weight or set.weight

            session.add(set)
            session.commit()
            session.refresh(set)

            return SetRead(**set.dict())
