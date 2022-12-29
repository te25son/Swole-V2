from dotenv import load_dotenv

from swole_v2.app import SwoleApp
from swole_v2.settings import Settings

from . import ROOT_PATH


def test_uses_correct_settings(test_app: SwoleApp) -> None:
    # pytest automatically creates/loads test env vars based on settings in pyproject.toml
    test_settings = Settings()
    # override the env vars created by pytest with those of another group of settings
    load_dotenv(dotenv_path=ROOT_PATH.joinpath(".env"), override=True)
    dev_settings = Settings()

    assert test_app.settings.dict() != dev_settings.dict()
    assert test_app.settings.dict() == test_settings.dict()
