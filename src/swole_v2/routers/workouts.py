from fastapi import APIRouter, Depends

from ..database.repositories import WorkoutRepository
from ..models import User
from ..schemas import (
    SuccessResponse,
    WorkoutCreate,
    WorkoutDelete,
    WorkoutDetail,
    WorkoutGetAllExercises,
    WorkoutUpdate,
)
from ..security import get_current_active_user

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post("/all", response_model=SuccessResponse)
def get_all(
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=respository.get_all(current_user.id))


@router.post("/detail", response_model=SuccessResponse)
def detail(
    data: WorkoutDetail,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[respository.detail(current_user.id, data.workout_id)])


@router.post("/create", response_model=SuccessResponse)
def create(
    data: WorkoutCreate,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[respository.create(current_user.id, data)])


@router.post("/delete", response_model=SuccessResponse)
def delete(
    data: WorkoutDelete,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    respository.delete(current_user.id, data.workout_id)
    return SuccessResponse()


@router.post("/update", response_model=SuccessResponse)
def update(
    data: WorkoutUpdate,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[respository.update(current_user.id, data)])


@router.post("/exercises", response_model=SuccessResponse)
def get_all_exercises(
    data: WorkoutGetAllExercises,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=respository.get_all_exercises(current_user.id, data))
