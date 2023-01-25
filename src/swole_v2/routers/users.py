from fastapi import APIRouter, Depends

from ..dependencies.auth import get_current_active_user
from ..models import User, UserRead
from ..schemas import SuccessResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/profile", response_model=SuccessResponse)
async def profile(current_user: User = Depends(get_current_active_user)) -> SuccessResponse:
    return SuccessResponse(results=[UserRead(**current_user.dict())])
