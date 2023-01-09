from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from ..models import Exercise, Workout


class Set(SQLModel, table=True):  # type: ignore
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)

    rep_count: int = Field(ge=1, le=500, nullable=False)
    weight: int = Field(ge=1, le=10000, nullable=False)

    exercise_id: UUID = Field(foreign_key="exercise.id")
    exercise_user_id: UUID = Field(foreign_key="exercise.user_id")
    exercise: "Exercise" = Relationship(
        back_populates="sets",
        sa_relationship_kwargs=dict(
            primaryjoin="and_(Set.exercise_id==Exercise.id, Set.exercise_user_id==Exercise.user_id)"
        ),
    )

    workout_id: UUID = Field(foreign_key="workout.id")
    workout_user_id: UUID = Field(foreign_key="workout.user_id")
    workout: "Workout" = Relationship(
        back_populates="sets",
        sa_relationship_kwargs=dict(
            primaryjoin="and_(Set.workout_id==Workout.id, Set.workout_user_id==Workout.user_id)"
        ),
    )

    __table_args__ = (
        Index(
            "search_by_workout_and_exercise_index",
            "exercise_id",
            "exercise_user_id",
            "workout_id",
            "workout_user_id"
        ),
        CheckConstraint("workout_user_id == exercise_user_id"),
    )


class SetRead(SQLModel):
    rep_count: int
    weight: int
