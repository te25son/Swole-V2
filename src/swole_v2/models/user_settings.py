import enum
from uuid import UUID

from pydantic import BaseModel


class WeightUnit(enum.IntEnum):
    KGS = 0
    LBS = 1


class UserSettings(BaseModel):
    id: UUID
    weight_unit: WeightUnit


class UserSettingsRead(BaseModel):
    weight_unit: WeightUnit
