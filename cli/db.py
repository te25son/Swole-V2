import asyncio
import os
from pathlib import Path
from random import choice

import click
from dotenv import load_dotenv

from swole_v2.dependencies.passwords import hash_password
from swole_v2.dependencies.settings import get_settings
from swole_v2.settings import Settings
from tests.factories import Sample

ROOT_PATH = Path(__file__).resolve().parents[1]


@click.command()
def seed() -> None:
    """Seeds the development database."""
    if os.getenv("EDGEDB_INSTANCE") is None:
        load_dotenv(dotenv_path=ROOT_PATH.joinpath(".env"), override=True)
    settings = get_settings()
    try:
        click.secho(f"Seeding {settings.EDGEDB_INSTANCE} instance...", fg="blue", bold=True)
        asyncio.run(create_instances(settings))
        click.secho("Seeding complete.", fg="green", bold=True)
    except Exception as e:
        click.secho(f"Exception when adding instances to database:\n\n {str(e)}", fg="red")


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
        user = choice([*users, admin])

        # Create some workouts without exercises
        workouts = await sample.workouts(user=user, size=choice(range(10, 20)))
        # Create some exercises without workouts
        exercises = await sample.exercises(user=user, size=choice(range(10, 20)))
        # Add some sets to the exercises
        for _ in range(5):
            await sample.sets(workout=choice(workouts), exercise=choice(exercises), size=choice(range(0, 10)))
