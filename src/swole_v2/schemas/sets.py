from __future__ import annotations

from pydantic import BaseModel

from .validators import ID, RepCount, Weight


class SetGetAll(BaseModel):
    workout_id: ID
    exercise_id: ID


class SetAdd(BaseModel):
    rep_count: RepCount
    weight: Weight
    workout_id: ID
    exercise_id: ID


class SetDelete(BaseModel):
    set_id: ID


class SetUpdate(BaseModel):
    set_id: ID
    rep_count: RepCount | None = None
    weight: Weight | None = None
