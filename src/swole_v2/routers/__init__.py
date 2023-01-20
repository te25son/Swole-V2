from fastapi import APIRouter

from . import auth, exercises, sets, users, workouts

router = APIRouter(prefix="/api/v2")
router.include_router(auth.router)
router.include_router(exercises.router)
router.include_router(sets.router)
router.include_router(users.router)
router.include_router(workouts.router)
