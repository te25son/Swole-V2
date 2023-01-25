from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..database.repositories import UserRepository
from ..errors.messages import INACTIVE_USER
from ..models import User


async def get_current_active_user(
    authorization: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    repository: UserRepository = Depends(UserRepository.as_dependency),
) -> User:
    current_user = await repository.get_current_user(authorization.credentials)
    if current_user.disabled:
        raise HTTPException(status_code=400, detail=INACTIVE_USER)
    return current_user
