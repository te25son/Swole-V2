from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel

if TYPE_CHECKING:
    from . import ExerciseRead


class Workout(BaseModel):
    id: UUID | None
    name: str
    date: date
    exercises: list["ExerciseRead"] | None


class WorkoutRead(BaseModel):
    name: str | None
    date: date | None
