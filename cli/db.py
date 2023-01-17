from random import choice
from typing import TypeVar

import click
from click import Context

from swole_v2.helpers import hash_password
from swole_v2.settings import Settings, get_settings
from tests.factories import Sample

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
    pass


@db.command()
@click.pass_obj
def seed(context: CliContext) -> None:
    """
    Seeds the database if not PROD
    """
    if context.environment == Environments.PROD:
        raise click.ClickException("Cannot seed production environment.")

    try:
        create_instances(context.settings)
    except Exception as e:
        click.secho(f"Exception when adding instances to database: {str(e)}", fg="red")


def create_instances(settings: Settings) -> None:
    sample = Sample()
    # Create admin user
    sample.user(
        username=settings.DUMMY_USERNAME,
        hashed_password=hash_password(settings.DUMMY_PASSWORD),
        disabled=False,
    )
    # Create other users
    users = sample.users(size=10)

    # Create workout and exercise instances
    for _ in range(20):
        user = choice(users)

        # Create some workouts without exercises
        sample.workouts(user=user, size=choice(range(0, 10)))
        # Create some exercises without workouts
        sample.exercises(user=user, size=choice(range(0, 10)))
