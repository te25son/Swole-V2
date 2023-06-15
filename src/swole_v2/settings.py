from __future__ import annotations

from pydantic import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str
    EDGEDB_INSTANCE: str
    EDGEDB_SECRET_KEY: str | None = None  # Only needed for production
    DUMMY_USERNAME: str = "username"
    DUMMY_PASSWORD: str = "password"
    HASH_ALGORITHM: str = "HS256"
    TOKEN_EXPIRE: int = 1440  # Default is one day in minutes
