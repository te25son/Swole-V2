from fastapi import APIRouter, Depends

from ..database.repositories import WorkoutRepository
from ..models import SuccessResponse, User, WorkoutCreate, WorkoutUpdate
from ..security import get_current_active_user

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post("/all", response_model=SuccessResponse)
def get_all(
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=respository.get_all(current_user.id))


@router.post("/detail/{workout_id}", response_model=SuccessResponse)
def detail(
    workout_id: str,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[respository.detail(current_user.id, workout_id)])


@router.post("/create", response_model=SuccessResponse)
def create(
    workout: WorkoutCreate,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[respository.create(current_user.id, workout)])


@router.post("/delete/{workout_id}", response_model=SuccessResponse)
def delete(
    workout_id: str,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    respository.delete(current_user.id, workout_id)
    return SuccessResponse()


@router.post("/update/{workout_id}", response_model=SuccessResponse)
def update(
    workout_id: str,
    update_data: WorkoutUpdate,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[respository.update(current_user.id, workout_id, update_data)])
