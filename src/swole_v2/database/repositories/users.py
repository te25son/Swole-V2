from uuid import UUID

from sqlmodel import Session, select

from ...models import Result, User
from .base import BaseRepository

USER_WITH_ID_NOT_FOUND = "No user with given id could be found."


class UserRepository(BaseRepository):
    def get_user_by_id(self, user_id: UUID | None) -> Result:
        with Session(self.database) as session:
            result = session.exec(select(User).where(User.id == user_id)).one_or_none()

            if result:
                return Result(success=True, product=[result])
            return Result(success=False, message=USER_WITH_ID_NOT_FOUND)
