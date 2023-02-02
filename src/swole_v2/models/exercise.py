from datetime import date
from uuid import UUID

from pydantic import BaseModel, validator


class Exercise(BaseModel):
    name: str
    id: UUID | None
    notes: str | None


class ExerciseRead(BaseModel):
    name: str | None
    notes: str | None


class ExerciseProgressRead(BaseModel):
    name: str
    date: date
    avg_rep_count: float
    avg_weight: float
    max_weight: int

    @validator("avg_rep_count", "avg_weight")
    def round_averages(cls, value: float) -> float:
        return round(value, 2)
