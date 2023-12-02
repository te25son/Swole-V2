from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from ..database.repositories import SetRepository
from ..dependencies.auth import get_current_active_user
from ..schemas import SetAdd, SetDelete, SetGetAll, SetUpdate, SuccessResponse

if TYPE_CHECKING:
    from ..models import User

router = APIRouter(prefix="/sets", tags=["sets"])


@router.post("/all", response_model=SuccessResponse)
async def get_all_by_workout_and_exercise(
    data: SetGetAll,
    current_user: User = Depends(get_current_active_user),
    respository: SetRepository = Depends(SetRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=await respository.get_all(current_user.id, data))


@router.post("/add", response_model=SuccessResponse)
async def add_to_workout_and_exercise(
    data: list[SetAdd],
    current_user: User = Depends(get_current_active_user),
    respository: SetRepository = Depends(SetRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=await respository.add(current_user.id, data))


@router.post("/delete", response_model=SuccessResponse)
async def delete(
    data: SetDelete,
    current_user: User = Depends(get_current_active_user),
    respository: SetRepository = Depends(SetRepository.as_dependency),
) -> SuccessResponse:
    await respository.delete(current_user.id, data)
    return SuccessResponse()


@router.post("/update", response_model=SuccessResponse)
async def update(
    data: SetUpdate,
    current_user: User = Depends(get_current_active_user),
    respository: SetRepository = Depends(SetRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[await respository.update(current_user.id, data)])
