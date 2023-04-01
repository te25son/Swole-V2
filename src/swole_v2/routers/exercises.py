from __future__ import annotations

from fastapi import APIRouter, Depends

from ..database.repositories import ExerciseRepository
from ..dependencies.auth import get_current_active_user
from ..models import User
from ..schemas import ExerciseCreate, ExerciseDelete, ExerciseDetail, ExerciseProgress, ExerciseUpdate, SuccessResponse

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.post("/all", response_model=SuccessResponse)
async def get_all_by_user(
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=await respository.get_all(current_user.id))


@router.post("/detail", response_model=SuccessResponse)
async def detail(
    data: ExerciseDetail,
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[await respository.detail(current_user.id, data.exercise_id)])


@router.post("/create", response_model=SuccessResponse)
async def create(
    data: ExerciseCreate,
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[await respository.create(current_user.id, data)])


@router.post("/update", response_model=SuccessResponse)
async def update(
    data: ExerciseUpdate,
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[await respository.update(current_user.id, data)])


@router.post("/delete", response_model=SuccessResponse)
async def delete(
    data: ExerciseDelete,
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    await respository.delete(current_user.id, data)
    return SuccessResponse()


@router.post("/progress", response_model=SuccessResponse)
async def progress(
    data: ExerciseProgress,
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=await respository.progress(current_user.id, data))
