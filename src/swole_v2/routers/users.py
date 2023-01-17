from fastapi import APIRouter, Depends

from ..models import User, UserRead
from ..security import get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/profile", response_model=UserRead)
async def profile(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user
