from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_CONNECTION: str
    SECRET_KEY: str
    DUMMY_USERNAME: str = "username"
    DUMMY_PASSWORD: str = "password"
    HASH_ALGORITHM: str = "HS256"
    TOKEN_EXPIRE: int = 30


@lru_cache()
def get_settings() -> Settings:
    return Settings()
