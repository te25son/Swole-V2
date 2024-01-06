from __future__ import annotations

from pydantic import BaseModel

from .validators import ID, NonEmptyString


class ExerciseDetail(BaseModel):
    exercise_id: ID


class ExerciseCreate(BaseModel):
    name: NonEmptyString
    notes: str | None = None


class ExerciseUpdate(BaseModel):
    exercise_id: ID
    name: NonEmptyString | None = None
    notes: str | None = None


class ExerciseDelete(BaseModel):
    exercise_id: ID


class ExerciseProgress(BaseModel):
    exercise_id: ID
