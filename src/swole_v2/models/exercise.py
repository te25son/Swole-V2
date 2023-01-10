from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from . import Workout, User, Set

from ..models.links import WorkoutExerciseLink


class Exercise(SQLModel, table=True):  # type: ignore
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)

    user_id: UUID = Field(foreign_key="user.id")
    user: "User" = Relationship(back_populates="exercises")

    sets: list["Set"] = Relationship(
        back_populates="exercise",
        sa_relationship_kwargs=dict(
            primaryjoin="and_(Exercise.id==Set.exercise_id, Exercise.user_id==Set.exercise_user_id)",
            cascade="all, delete-orphan",
        ),
    )

    workouts: list["Workout"] = Relationship(
        back_populates="exercises",
        link_model=WorkoutExerciseLink,
        sa_relationship_kwargs=dict(
            primaryjoin="and_(Exercise.id==WorkoutExerciseLink.exercise_id, Exercise.user_id==WorkoutExerciseLink.exercise_user_id)",
            secondaryjoin="and_(Workout.id==WorkoutExerciseLink.workout_id, Workout.user_id==WorkoutExerciseLink.workout_user_id)",
        ),
    )

    __table_args__ = (
        Index("search_exercise_by_id_and_user_id", "id", "user_id"),
        UniqueConstraint("user_id", "name", name="user_id_and_name_uc"),
    )


class ExerciseRead(SQLModel):
    name: str
