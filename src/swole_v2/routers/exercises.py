from fastapi import APIRouter, Depends

from ..database.repositories import ExerciseRepository
from ..models import User
from ..schemas import (
    ExerciseAddToWorkout,
    ExerciseCreate,
    ExerciseDelete,
    ExerciseDetail,
    ExerciseUpdate,
    SuccessResponse,
)
from ..security import get_current_active_user

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.post("/all", response_model=SuccessResponse)
def get_all_by_workout(
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=respository.get_all(current_user.id))


@router.post("/detail", response_model=SuccessResponse)
def detail(
    data: ExerciseDetail,
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[respository.detail(current_user.id, data.exercise_id)])


@router.post("/create", response_model=SuccessResponse)
def create(
    data: ExerciseCreate,
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[respository.create(current_user.id, data)])


@router.post("/add", response_model=SuccessResponse)
def add_to_workout(
    data: ExerciseAddToWorkout,
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[respository.add_to_workout(current_user.id, data)])


@router.post("/update", response_model=SuccessResponse)
def update(
    data: ExerciseUpdate,
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[respository.update(current_user.id, data)])


@router.post("/delete", response_model=SuccessResponse)
def delete(
    data: ExerciseDelete,
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    respository.delete(current_user.id, data)
    return SuccessResponse()
