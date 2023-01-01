from uuid import UUID

from sqlmodel import Session, select

from ...exceptions import BusinessError
from ...models import User, UserRead
from .base import BaseRepository

USER_WITH_ID_NOT_FOUND = "No user with given id could be found."


class UserRepository(BaseRepository):
    def get_user_by_id(self, user_id: UUID | None) -> UserRead:
        with Session(self.database) as session:
            user = session.exec(select(User).where(User.id == user_id)).one_or_none()

            if not user:
                raise BusinessError(USER_WITH_ID_NOT_FOUND)
            return UserRead(**user.dict())
