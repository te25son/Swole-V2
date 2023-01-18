from uuid import UUID

from pydantic import BaseModel


class Exercise(BaseModel):
    name: str
    id: UUID | None
    notes: str | None


class ExerciseRead(BaseModel):
    name: str | None
    notes: str | None
