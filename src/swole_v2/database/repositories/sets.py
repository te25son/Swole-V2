from uuid import UUID

from sqlalchemy import and_
from sqlmodel import Session, select

from ...models import Set, SetRead
from ...schemas import SetGetAll
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
