<h1 align="center">Swole V2</h1>

<p align="center">API for tracking workouts</p>

# Setup

You will need to install four dependencies in order to run the project locally.

1. [poetry](https://python-poetry.org/docs/#installation)
2. [pre-commit](https://pre-commit.com/#installation)
3. [just](https://github.com/casey/just#packages)
4. [edgedb](https://www.edgedb.com/install)

Once installed, clone this repo with `git clone git@github.com:te25son/Swole-V2.git` and navigate your way into the project's root folder `cd Swole-V2`.

Setup the environment by running `just setup`, and then activate the virtual environment with `poetry shell`.

You should now be able to run all the commands available within the project. Try it out by opening the development database's UI with `db dev ui`.
