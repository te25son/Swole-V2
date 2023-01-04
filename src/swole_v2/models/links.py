from uuid import UUID

from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel


class WorkoutExerciseLink(SQLModel, table=True):  # type: ignore
    workout_id: UUID = Field(foreign_key="workout.id", primary_key=True)
    exercise_id: UUID = Field(foreign_key="exercise.id", primary_key=True)

    workout_user_id: UUID
    exercise_user_id: UUID

    __table_args__ = (CheckConstraint("workout_user_id == exercise_user_id"),)
