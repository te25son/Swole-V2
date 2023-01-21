from swole_v2.models.exercise import (
    Exercise,
    ExerciseProgressRead,
    ExerciseRead,
)
from swole_v2.models.set import Set, SetRead
from swole_v2.models.token import Token, TokenData
from swole_v2.models.user import User, UserRead
from swole_v2.models.workout import Workout, WorkoutRead

Set.update_forward_refs(Workout=Workout, Exercise=Exercise)
Workout.update_forward_refs(Exercise=Exercise)

__all__ = [
    "User",
    "UserRead",
    "Token",
    "TokenData",
    "Workout",
    "WorkoutRead",
    "Exercise",
    "ExerciseRead",
    "ExerciseProgressRead",
    "Set",
    "SetRead",
]
