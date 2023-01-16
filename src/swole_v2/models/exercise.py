from uuid import UUID

from pydantic import BaseModel


class Exercise(BaseModel):
    id: UUID | None
    name: str


class ExerciseRead(BaseModel):
    name: str | None
