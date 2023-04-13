from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ..database.repositories import WorkoutRepository
from ..dependencies.auth import get_current_active_user
from ..models import User
from ..schemas import (
    SuccessResponse,
    WorkoutAddExercise,
    WorkoutCopy,
    WorkoutCreate,
    WorkoutDelete,
    WorkoutDetail,
    WorkoutUpdate,
)

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post("/all", response_model=SuccessResponse)
async def get_all(
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=await respository.get_all(current_user.id))


@router.post("/detail", response_model=SuccessResponse)
async def detail(
    data: list[WorkoutDetail],
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
    with_exercises: Annotated[bool, Query()] = False,
) -> SuccessResponse:
    return SuccessResponse(results=await respository.detail(current_user.id, data, with_exercises))


@router.post("/create", response_model=SuccessResponse)
async def create(
    data: list[WorkoutCreate],
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=await respository.create(current_user.id, data))


@router.post("/delete", response_model=SuccessResponse)
async def delete(
    data: list[WorkoutDelete],
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    await respository.delete(current_user.id, data)
    return SuccessResponse()


@router.post("/update", response_model=SuccessResponse)
async def update(
    data: list[WorkoutUpdate],
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=await respository.update(current_user.id, data))


@router.post("/add-exercises", response_model=SuccessResponse)
async def add_exercises(
    data: list[WorkoutAddExercise],
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=await respository.add_exercises(current_user.id, data))


@router.post("/copy", response_model=SuccessResponse)
async def copy(
    data: list[WorkoutCopy],
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=await respository.copy(current_user.id, data))
