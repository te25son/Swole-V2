from fastapi import APIRouter, Depends

from ..database.repositories import UserRepository
from ..models import Token
from ..schemas import UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def token(
    data: UserLogin,
    repository: UserRepository = Depends(UserRepository.as_dependency),
) -> Token:
    return await repository.get_token(data.username, data.password)
