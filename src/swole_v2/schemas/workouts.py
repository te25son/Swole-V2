from __future__ import annotations

from pydantic import BaseModel

from .validators import ID, Date, NonEmptyString


class WorkoutDetail(BaseModel):
    workout_id: ID


class WorkoutCreate(BaseModel):
    name: NonEmptyString
    date: Date


class WorkoutUpdate(BaseModel):
    workout_id: ID
    name: NonEmptyString | None = None
    date: Date | None = None


class WorkoutDelete(BaseModel):
    workout_id: ID


class WorkoutAddExercise(BaseModel):
    workout_id: ID
    exercise_id: ID


class WorkoutCopy(BaseModel):
    workout_id: ID
    date: Date
