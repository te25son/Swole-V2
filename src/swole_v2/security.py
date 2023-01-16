from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from .database.database import get_client
from .helpers import verify_password
from .models import TokenData, User
from .settings import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@lru_cache()
def get_user(username: str) -> User | None:
    result = get_client().query_single_json("SELECT User FILTER .username = <str>$username", username=username)
    return User.parse_raw(result) if result else None


def authenticate_user(username: str, password: str) -> User | None:
    if not (user := get_user(username)):
        return None
    if not verify_password(password, user.hashed_password):  # type: ignore
        return None
    return user


def create_access_token(data: dict[str, Any]) -> str:
    settings = get_settings()
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(minutes=settings.TOKEN_EXPIRE)})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.HASH_ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.HASH_ALGORITHM])
        username = payload.get("username")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
