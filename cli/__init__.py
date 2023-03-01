import os
from enum import Enum
from pathlib import Path

import toml
from dotenv import load_dotenv
from pydantic import BaseModel

from swole_v2.settings import Settings

ROOT_PATH = Path(__file__).resolve().parents[1]


class Environments(Enum):
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
        case Environments.DEV:
            load_dotenv(dotenv_path=ROOT_PATH.joinpath(".env"), override=True)
        case Environments.TEST:
            load_test_env()


def load_test_env() -> None:
    pyproject_file = ROOT_PATH.joinpath("pyproject.toml")
    with open(pyproject_file, "r") as file:
        data = toml.load(file)

    test_envs: list[str] = data["tool"]["pytest"]["ini_options"]["env"]
    for env in test_envs:
        parts = env.partition("=")
        key = parts[0].strip().upper()
        value = parts[2].strip()
        os.environ[key] = value
