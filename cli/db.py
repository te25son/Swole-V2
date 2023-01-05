from random import choice
from typing import TypeVar

import click
from click import Context
from sqlmodel import Session, SQLModel, create_engine

from swole_v2.helpers import hash_password
from swole_v2.settings import Settings, get_settings
from tests.factories import ExerciseFactory, UserFactory, WorkoutFactory

from . import CliContext, Environments, load_environment_variables

T = TypeVar("T")


@click.group()
@click.argument("env", type=click.Choice([e.value for e in Environments], case_sensitive=False))
@click.pass_context
def db(context: Context, env: str) -> None:
    """
    Base command from which to run database commands.
    """
    context.ensure_object(dict)

    load_environment_variables(environment := Environments.from_string(env))

    context.obj = CliContext(settings=get_settings(), environment=environment)


@db.command()
@click.pass_obj
def init(context: CliContext) -> None:
    """
    Initializes the database if not initialized already.
    """
    # Must import models in order to initialize the database
    from swole_v2 import models  # noqa F401

    should_echo = False if context.environment == Environments.PROD else True

    SQLModel.metadata.create_all(create_engine(context.settings.DB_CONNECTION, echo=should_echo))


@db.command()
@click.pass_obj
def seed(context: CliContext) -> None:
    """
    Seeds the database if not PROD
    """
    if context.environment == Environments.PROD:
        raise click.ClickException("Cannot seed production environment.")

    with Session(create_engine(context.settings.DB_CONNECTION, echo=True)) as session:
        try:
            create_instances(context.settings, session)
        except Exception as e:
            click.secho(f"Exception when adding instances to database: {str(e)}", fg="red")


def create_instances(settings: Settings, session: Session) -> None:
    # Create user instances
    users = UserFactory.create_batch_sync(10)
    admin_user = UserFactory.create_sync(
        username=settings.DUMMY_USERNAME,
        hashed_password=hash_password(settings.DUMMY_PASSWORD),
        disabled=False,
    )
    all_users = users + [admin_user]

    # Create workout and exercise instances
    for _ in range(20):
        user = choice(all_users)
        WorkoutFactory.create_sync(
            user=user,
            exercises=ExerciseFactory.create_batch_sync(user=user, size=choice(range(0, 10)))
        )


def random_chunk(sequence: list[T]) -> list[list[T]]:
    chunks = []
    chunk_size = choice(range(1, 5))
    for i in range(0, len(sequence), chunk_size):
        chunks.append(sequence[i : i + chunk_size])

    chunks.append([])  # append empty list so there can be a random empty choice
    return chunks
