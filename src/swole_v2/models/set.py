from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from pydantic import BaseModel

if TYPE_CHECKING:
    from . import Exercise, Workout


class Set(BaseModel):
    id: UUID | None = None
    rep_count: int
    weight: int
    workout: Optional["Workout"] = None
    exercise: Optional["Exercise"] = None


class SetRead(BaseModel):
    id: UUID
    rep_count: int | None = None
    weight: int | None = None
