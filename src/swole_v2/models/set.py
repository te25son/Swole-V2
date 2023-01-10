from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from . import WorkoutExerciseLink


class Set(SQLModel, table=True):  # type: ignore
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)

    rep_count: int = Field(ge=1, le=500, nullable=False)
    weight: int = Field(ge=1, le=10000, nullable=False)

    workout_id: UUID = Field(foreign_key="workoutexerciselink.workout_id")
    exercise_id: UUID = Field(foreign_key="workoutexerciselink.exercise_id")
    workout_exercise_link: "WorkoutExerciseLink" = Relationship(
        back_populates="sets",
        sa_relationship_kwargs=dict(
            primaryjoin="and_(Set.workout_id==WorkoutExerciseLink.workout_id, Set.exercise_id==WorkoutExerciseLink.exercise_id)"
        ),
    )


class SetRead(SQLModel):
    rep_count: int
    weight: int
