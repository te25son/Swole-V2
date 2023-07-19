from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from . import Exercise


class Workout(BaseModel):
    id: UUID | None = None
    name: str
    date: datetime.date
    exercises: list["Exercise"] = Field(default=[])


class WorkoutRead(BaseModel):
    id: UUID
    name: str | None = None
    date: datetime.date | None = None
