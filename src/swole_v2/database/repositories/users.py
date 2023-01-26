from datetime import datetime, timedelta
from typing import Any

from edgedb import AsyncIOClient
from fastapi import Depends, HTTPException
from jose import JWTError, jwt

from ...database.database import get_async_client
from ...dependencies.passwords import verify_password
from ...dependencies.settings import get_settings
from ...errors.messages import (
    COULD_NOT_VALIDATE_CREDENTIALS,
    INCORRECT_USERNAME_OR_PASSWORD,
)
from ...models import Token, TokenData, User
from ...settings import Settings


class UserRepository:
    def __init__(self, client: AsyncIOClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    @classmethod
    async def as_dependency(
        cls,
        client: AsyncIOClient = Depends(get_async_client),
        settings: Settings = Depends(get_settings),
    ) -> "UserRepository":
        return cls(client, settings)

    async def get_token(self, username: str, password: str) -> Token:
        if (user := await self.authenticate_user(username, password)) is None:
            raise HTTPException(status_code=401, detail=INCORRECT_USERNAME_OR_PASSWORD)

        access_token = await self.create_access_token({"username": user.username})
        return Token(access_token=access_token)

    async def get_current_user(self, token: str) -> User:
        credentials_exception = HTTPException(status_code=401, detail=COULD_NOT_VALIDATE_CREDENTIALS)
        try:
            payload = jwt.decode(token, self.settings.SECRET_KEY, algorithms=[self.settings.HASH_ALGORITHM])
            username = payload.get("username")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception

        if (user := await self.get_user_by_username(token_data.username)) is None:
            raise credentials_exception
        return user

    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.client.query_single_json(
            """
            SELECT User {id, username, hashed_password, email, disabled}
            FILTER .username = <str>$username
            """,
            username=username,
        )
        return User.parse_raw(result) if result else None

    async def authenticate_user(self, username: str, password: str) -> User | None:
        user = await self.get_user_by_username(username)
        if user is None or not await verify_password(password, user.hashed_password):  # type: ignore
            return None
        return user

    async def create_access_token(self, data: dict[str, Any]) -> str:
        to_encode = data.copy()
        to_encode.update({"exp": datetime.utcnow() + timedelta(minutes=self.settings.TOKEN_EXPIRE)})
        encoded_jwt = jwt.encode(to_encode, self.settings.SECRET_KEY, algorithm=self.settings.HASH_ALGORITHM)
        return encoded_jwt
