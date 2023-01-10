from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from . import User, WorkoutExerciseLink


class Exercise(SQLModel, table=True):  # type: ignore
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)

    user_id: UUID = Field(foreign_key="user.id")
    user: "User" = Relationship(back_populates="exercises")

    workout_links: list["WorkoutExerciseLink"] = Relationship(
        back_populates="exercise",
        sa_relationship_kwargs=dict(
            primaryjoin="and_(Exercise.id==WorkoutExerciseLink.exercise_id, Exercise.user_id==WorkoutExerciseLink.exercise_user_id)"
        ),
    )

    __table_args__ = (
        Index("search_exercise_by_id_and_user_id", "id", "user_id"),
        UniqueConstraint("user_id", "name", name="user_id_and_name_uc"),
    )


class ExerciseRead(SQLModel):
    name: str
