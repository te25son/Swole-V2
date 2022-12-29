import nox
from nox.sessions import Session

python_versions = ["3.10"]
locations = ("src", "tests", "cli", "noxfile.py")


@nox.session(python=python_versions)
def test(session: Session) -> None:
    args = session.posargs or ["--cov"]
    # Poetry is not a part of the environment created by Nox, so we specify external
    # to avoid warnings about external commands leaking into the isolated test environments.
    session.run("poetry", "install", "--without", "stubs", external=True)
    session.run("pytest", *args)


@nox.session(python=python_versions[0], tags=["check"])
def lint(session: Session) -> None:
    args = session.posargs or locations
    session.install("flake8", "Flake8-pyproject", "flake8-black", "flake8-import-order")
    session.run("flake8", *args)


@nox.session(python=python_versions[0], tags=["check"])
def mypy(session: Session) -> None:
    args = session.posargs or locations
    session.run("poetry", "install", "--only", "stubs", external=True)
    session.install("mypy")
    session.run("mypy", *args)


@nox.session(python=python_versions[0], tags=["clean"])
def isort(session: Session) -> None:
    args = session.posargs or locations
    session.install("isort")
    session.run("isort", *args)


@nox.session(python=python_versions[0], tags=["clean"])
def black(session: Session) -> None:
    args = session.posargs or locations
    session.install("black")
    session.run("black", *args)
