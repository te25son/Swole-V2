from enum import Enum
from pathlib import Path

import click
from dotenv import load_dotenv
from pydantic import BaseModel

from swole_v2.settings import Settings

ROOT_PATH = Path(__file__).resolve().parents[1]


class Environments(Enum):
    PROD = "prod"
    DEV = "dev"
    TEST = "test"

    @staticmethod
    def from_string(value: str) -> "Environments":
        return Environments[value.upper()]


class CliContext(BaseModel):
    settings: Settings
    environment: Environments

    class Config:
        validate_assignment = True


def load_environment_variables(environment: Environments) -> None:
    match environment:
        case Environments.PROD:
            click.ClickException("Prod not implemented")
        case Environments.DEV:
            env_file = ".env"
        case Environments.TEST:
            env_file = "test.env"

    load_dotenv(dotenv_path=ROOT_PATH.joinpath(env_file), override=True)
