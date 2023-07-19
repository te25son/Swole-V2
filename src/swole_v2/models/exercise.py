from __future__ import annotations

import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class Exercise(BaseModel):
    name: str
    id: UUID | None = None
    notes: str | None = None


class ExerciseRead(BaseModel):
    id: UUID
    name: str | None = None
    notes: str | None = None


class ExerciseProgressReportData(BaseModel):
    date: datetime.date
    avg_rep_count: float
    avg_weight: float
    max_weight: int

    @field_validator("avg_rep_count", "avg_weight")
    def round_averages(cls, value: float) -> float:
        return round(value, 2)


class ExerciseProgressReport(BaseModel):
    exercise_name: str
    data: list[ExerciseProgressReportData] | None = Field(default=[])
