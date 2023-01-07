from uuid import UUID

from pydantic import BaseModel

from .validators import check_is_uuid, schema_validator


class SetGetAll(BaseModel):
    workout_id: UUID
    exercise_id: UUID

    _check_ids = schema_validator("workout_id", "exercise_id")(check_is_uuid)
