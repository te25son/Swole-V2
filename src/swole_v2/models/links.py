from uuid import UUID

from sqlmodel import Field, SQLModel


class WorkoutExerciseLink(SQLModel, table=True):  # type: ignore
    workout_id: UUID = Field(foreign_key="workout.id", primary_key=True)
    exercise_id: UUID = Field(foreign_key="exercise.id", primary_key=True)
