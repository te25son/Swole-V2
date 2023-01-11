from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Column, ForeignKey
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from . import Exercise, Set, Workout


class WorkoutExerciseLink(SQLModel, table=True):  # type: ignore
    workout_id: UUID = Field(sa_column=Column(ForeignKey("workout.id", ondelete="CASCADE"), primary_key=True))
    workout_user_id: UUID = Field(sa_column=Column(ForeignKey("workout.user_id", ondelete="CASCADE")))
    workout: "Workout" = Relationship(
        back_populates="exercise_links",
        sa_relationship_kwargs=dict(
            primaryjoin="and_(WorkoutExerciseLink.workout_id==Workout.id, WorkoutExerciseLink.workout_user_id==Workout.user_id)"
        ),
    )

    exercise_id: UUID = Field(sa_column=Column(ForeignKey("exercise.id", ondelete="CASCADE"), primary_key=True))
    exercise_user_id: UUID = Field(sa_column=Column(ForeignKey("exercise.user_id", ondelete="CASCADE")))
    exercise: "Exercise" = Relationship(
        back_populates="workout_links",
        sa_relationship_kwargs=dict(
            primaryjoin="and_(WorkoutExerciseLink.exercise_id==Exercise.id, WorkoutExerciseLink.exercise_user_id==Exercise.user_id)"
        ),
    )

    sets: list["Set"] = Relationship(
        back_populates="workout_exercise_link",
        sa_relationship_kwargs=dict(
            primaryjoin="and_(WorkoutExerciseLink.workout_id==Set.workout_id, WorkoutExerciseLink.exercise_id==Set.exercise_id)",
            cascade="all, delete-orphan",
        ),
    )

    __table_args__ = (CheckConstraint("workout_user_id == exercise_user_id"),)
