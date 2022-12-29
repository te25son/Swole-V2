from sqlalchemy.future import Engine
from sqlmodel import create_engine

from ..settings import get_settings


def get_engine() -> Engine:
    return create_engine(get_settings().DB_CONNECTION, echo=True)
