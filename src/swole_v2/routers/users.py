from __future__ import annotations

from fastapi import APIRouter, Depends

from ..database.repositories import UserRepository
from ..dependencies.auth import get_current_active_user
from ..models import User, UserRead
from ..schemas import SuccessResponse, UserCreate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/create", response_model=SuccessResponse)
async def create(
    data: list[UserCreate], repository: UserRepository = Depends(UserRepository.as_dependency)
) -> SuccessResponse:
    return SuccessResponse(results=await repository.create(data))


@router.post("/profile", response_model=SuccessResponse)
async def profile(current_user: User = Depends(get_current_active_user)) -> SuccessResponse:
    return SuccessResponse(results=[UserRead(**current_user.dict())])
