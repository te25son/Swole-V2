from uuid import UUID

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, SQLModel


class WorkoutExerciseLink(SQLModel, table=True):  # type: ignore
    workout_id: UUID = Field(foreign_key="workout.id", primary_key=True)
    exercise_id: UUID = Field(foreign_key="exercise.id", primary_key=True)

    workout_user_id: UUID
    exercise_user_id: UUID

    __table_args__ = (
        UniqueConstraint("workout_id", "exercise_id", name="workout_id_and_exercise_id_uc"),
        CheckConstraint("workout_user_id == exercise_user_id"),
    )
