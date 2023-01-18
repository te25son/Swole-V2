from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str
    EDGEDB_INSTANCE: str
    EDGEDB_DSN: str
    DUMMY_USERNAME: str = "username"
    DUMMY_PASSWORD: str = "password"
    HASH_ALGORITHM: str = "HS256"
    TOKEN_EXPIRE: int = 30


@lru_cache()
def get_settings() -> Settings:
    return Settings()
