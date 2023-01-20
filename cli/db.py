import asyncio
from random import choice
import subprocess
from typing import TypeVar

import click
from click import Context

from swole_v2.helpers import hash_password
from swole_v2.settings import Settings, get_settings
from tests.factories import Sample

from . import CliContext, Environments, load_environment_variables

T = TypeVar("T")
EDGE_COMMAND = "edgedb"


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
    cmd = [EDGE_COMMAND, "instance", "create", context.settings.EDGEDB_INSTANCE]
    echo_command(cmd)
    subprocess.call(cmd)


@db.command()
@click.pass_obj
def ui(context: CliContext) -> None:
    """
    Opens the EdgeDB UI for the givin environment.
    """
    cmd = [EDGE_COMMAND, "--instance", context.settings.EDGEDB_INSTANCE, "ui"]
    echo_command(cmd)
    subprocess.call(cmd)


@db.command()
@click.pass_obj
def make_migration(context: CliContext) -> None:
    """
    Make a migration for the database.
    """
    cmd = [EDGE_COMMAND, "--instance", context.settings.EDGEDB_INSTANCE, "migration", "create"]
    echo_command(cmd)
    subprocess.call(cmd)


@db.command()
@click.pass_obj
def migrate(context: CliContext) -> None:
    """
    Migrate the database.
    """
    cmd = [EDGE_COMMAND, "--instance", context.settings.EDGEDB_INSTANCE, "migrate"]
    echo_command(cmd)
    subprocess.call(cmd)


@db.command()
@click.pass_obj
def seed(context: CliContext) -> None:
    """
    Seeds the database.
    """
    try:
        click.secho(f"Seeding {context.settings.EDGEDB_INSTANCE} instance...", fg="blue", bold=True)
        asyncio.run(create_instances(context.settings))
        click.secho("Seeding complete.", fg="green", bold=True)
    except Exception as e:
        click.secho(f"Exception when adding instances to database: {str(e)}", fg="red")


def echo_command(command: list[str]) -> None:
    click.secho(f"Invoking: {' '.join(command)}", fg="blue", bold=True)


async def create_instances(settings: Settings) -> None:
    sample = Sample()
    # Create admin user
    admin = await sample.user(
        username=settings.DUMMY_USERNAME,
        hashed_password=await hash_password(settings.DUMMY_PASSWORD),
        disabled=False,
    )
    # Create other users
    users = await sample.users(size=10)

    # Create workout and exercise instances
    for _ in range(20):
        user = choice(users + [admin])

        # Create some workouts without exercises
        workouts = await sample.workouts(user=user, size=choice(range(10, 20)))
        # Create some exercises without workouts
        exercises = await sample.exercises(user=user, size=choice(range(10, 20)))
        # Add some sets to the exercises
        for _ in range(5):
            await sample.sets(workout=choice(workouts), exercise=choice(exercises), size=choice(range(0, 10)))
