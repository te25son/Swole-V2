import enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, Integer
from sqlalchemy_utils import ChoiceType
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from . import User


class WeightUnit(enum.IntEnum):
    KGS = 0
    LBS = 1


class UserSettings(SQLModel, table=True):  # type: ignore
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    weight_unit: WeightUnit = Field(default=WeightUnit.KGS, sa_column=Column(ChoiceType(WeightUnit, impl=Integer())))

    user_id: UUID | None = Field(..., foreign_key="user.id")
    user: "User" = Relationship(back_populates="settings")


class UserSettingsRead(SQLModel):
    weight_unit: WeightUnit
