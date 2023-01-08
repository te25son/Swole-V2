from fastapi import APIRouter, Depends

from ..database.repositories import SetRepository
from ..models import User
from ..schemas import SetAdd, SetDelete, SetGetAll, SuccessResponse
from ..security import get_current_active_user

router = APIRouter(prefix="/sets", tags=["sets"])


@router.post("/all", response_model=SuccessResponse)
def get_all_by_workout_and_exercise(
    data: SetGetAll,
    current_user: User = Depends(get_current_active_user),
    respository: SetRepository = Depends(SetRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=respository.get_all(current_user.id, data))


@router.post("/add", response_model=SuccessResponse)
def add_to_workout_and_exercise(
    data: SetAdd,
    current_user: User = Depends(get_current_active_user),
    respository: SetRepository = Depends(SetRepository.as_dependency),
) -> SuccessResponse:
    return SuccessResponse(results=[respository.add(current_user.id, data)])


@router.post("/delete", response_model=SuccessResponse)
def delete(
    data: SetDelete,
    current_user: User = Depends(get_current_active_user),
    respository: SetRepository = Depends(SetRepository.as_dependency),
) -> SuccessResponse:
    respository.delete(current_user.id, data)
    return SuccessResponse()
