from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..errors.messages import INCORRECT_USERNAME_OR_PASSWORD
from ..models import Token
from ..security import authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(login_creds: OAuth2PasswordRequestForm = Depends()) -> Token:
    if not (user := await authenticate_user(login_creds.username, login_creds.password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INCORRECT_USERNAME_OR_PASSWORD,
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = await create_access_token(data={"username": user.username})

    return Token(access_token=access_token)
