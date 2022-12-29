from fastapi import APIRouter, Form, HTTPException, status

from ..models import Token
from ..security import authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(username: str = Form(), password: str = Form()) -> Token:
    if not (user := authenticate_user(username, password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"username": user.username})

    return Token(access_token=access_token)
