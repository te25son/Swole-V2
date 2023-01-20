from fastapi import APIRouter, Depends

from ..database.repositories import WorkoutRepository
from ..models import User
from ..schemas import (
    SuccessResponse,
    WorkoutAddExercise,
    WorkoutCreate,
    WorkoutDelete,
    WorkoutDetail,
    WorkoutGetAllExercises,
    WorkoutUpdate,
)
from ..security import get_current_active_user

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post("/all", response_model=SuccessResponse)
async def get_all(
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=await respository.get_all(current_user.id))


@router.post("/detail", response_model=SuccessResponse)
async def detail(
    data: WorkoutDetail,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[await respository.detail(current_user.id, data.workout_id)])


@router.post("/create", response_model=SuccessResponse)
async def create(
    data: WorkoutCreate,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[await respository.create(current_user.id, data)])


@router.post("/delete", response_model=SuccessResponse)
async def delete(
    data: WorkoutDelete,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    await respository.delete(current_user.id, data.workout_id)
    return SuccessResponse()


@router.post("/update", response_model=SuccessResponse)
async def update(
    data: WorkoutUpdate,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[await respository.update(current_user.id, data)])


@router.post("/add-exercise", response_model=SuccessResponse)
async def add_exercise(
    data: WorkoutAddExercise,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[await respository.add_exercise(current_user.id, data)])


@router.post("/exercises", response_model=SuccessResponse)
async def get_all_exercises(
    data: WorkoutGetAllExercises,
    current_user: User = Depends(get_current_active_user),
    respository: WorkoutRepository = Depends(WorkoutRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=await respository.get_all_exercises(current_user.id, data))
