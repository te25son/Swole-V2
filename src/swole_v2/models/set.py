from typing import TYPE_CHECKING, Optional
from uuid import UUID

from pydantic import BaseModel

if TYPE_CHECKING:
    from . import Exercise, Workout


class Set(BaseModel):
    id: UUID | None
    rep_count: int
    weight: int
    workout: Optional["Workout"]
    exercise: Optional["Exercise"]


class SetRead(BaseModel):
    rep_count: int | None
    weight: int | None
