from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .workout import Workout

from .links import WorkoutExerciseLink


class Exercise(SQLModel, table=True):  # type: ignore
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)

    workouts: list["Workout"] = Relationship(back_populates="exercises", link_model=WorkoutExerciseLink)
