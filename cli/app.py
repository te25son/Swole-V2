import click
from click.core import Context
import uvicorn

from swole_v2.settings import get_settings

from . import CliContext, Environments, load_environment_variables


@click.group()
@click.argument("env", type=click.Choice([env.value for env in Environments], case_sensitive=False))
@click.pass_context
def app(context: Context, env: str) -> None:
    """
    Base command for running the application.
    """
    context.ensure_object(dict)

    load_environment_variables(environment := Environments.from_string(env))

    context.obj = CliContext(settings=get_settings(), environment=environment)


@app.command()
@click.pass_obj
def run(context: CliContext) -> None:
    """
    Run the specified environment.
    """
    uvicorn.run("swole_v2.main:app", reload=True, port=5000)
