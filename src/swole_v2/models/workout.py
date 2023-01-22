from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from . import Exercise


class Workout(BaseModel):
    id: UUID | None
    name: str
    date: date
    exercises: list["Exercise"] = Field(default=[])


class WorkoutRead(BaseModel):
    name: str | None
    date: date | None
