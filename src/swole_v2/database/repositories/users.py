from uuid import UUID

from ...errors.exceptions import BusinessError
from ...errors.messages import NO_USER_FOUND
from ...models import UserRead
from .base import BaseRepository


class UserRepository(BaseRepository):
    async def get_user_by_id(self, user_id: UUID | None) -> UserRead:
        result = await self.client.query_single_json(
            """
            SELECT User {username, email}
            FILTER .id = <uuid>$user_id
            """,
            user_id=user_id,
        )

        if not result:
            raise BusinessError(NO_USER_FOUND)

        return UserRead.parse_raw(result)
