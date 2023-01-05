from uuid import UUID

from sqlmodel import Session, select

from ...errors.exceptions import BusinessError
from ...errors.messages import NO_USER_FOUND
from ...models import User, UserRead
from .base import BaseRepository


class UserRepository(BaseRepository):
    def get_user_by_id(self, user_id: UUID | None) -> UserRead:
        with Session(self.database) as session:
            user = session.exec(select(User).where(User.id == user_id)).one_or_none()

            if not user:
                raise BusinessError(NO_USER_FOUND)
            return UserRead(**user.dict())
