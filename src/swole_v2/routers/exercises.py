from fastapi import APIRouter, Depends

from ..database.repositories import ExerciseRepository
from ..models import ExerciseDetail, ExerciseGetAll, SuccessResponse, User, ExerciseCreate
from ..security import get_current_active_user

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.post("/all", response_model=SuccessResponse)
def get_all_by_workout(
    data: ExerciseGetAll,
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=respository.get_all(current_user.id, data.workout_id))


@router.post("/detail", response_model=SuccessResponse)
def detail(
    data: ExerciseDetail,
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[respository.detail(current_user.id, data.exercise_id)])


@router.post("/add", response_model=SuccessResponse)
def add(
    data: ExerciseCreate,
    current_user: User = Depends(get_current_active_user),
    respository: ExerciseRepository = Depends(ExerciseRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[respository.create(current_user.id, data)])
