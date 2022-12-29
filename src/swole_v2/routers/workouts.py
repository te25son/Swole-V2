from uuid import UUID

from fastapi import APIRouter, Depends

from ..database.repositories import WorkoutRepository
from ..models import SuccessResponse, User, WorkoutCreate, WorkoutUpdate
from ..security import get_current_active_user

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post("/all", response_model=SuccessResponse, response_model_exclude_unset=True)
def get_all(
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(result=respository.get_all(current_user.id))


@router.post("/add", response_model=SuccessResponse, response_model_exclude_unset=True)
def add(
    workout: WorkoutCreate,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(result=respository.create(current_user.id, workout))


@router.post("/delete/{workout_id}", response_model=SuccessResponse, response_model_exclude_unset=True)
def delete(
    workout_id: str,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(result=respository.delete(current_user.id, UUID(workout_id)))


@router.post("/update/{workout_id}", response_model=SuccessResponse, response_model_exclude_unset=True)
def update(
    workout_id: str,
    update_data: WorkoutUpdate,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(result=respository.update(current_user.id, UUID(workout_id), update_data))
