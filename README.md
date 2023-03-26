<h1 align="center">Swole V2</h1>

<p align="center">API for tracking workouts</p>

<div align="center">
  <a href="https://github.com/charliermarsh/ruff">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v0.json">
  </a>
  <a href="https://github.com/te25son/Swole-V2/actions/workflows/test.yml">
    <img src="https://github.com/te25son/Swole-V2/actions/workflows/test.yml/badge.svg">
  </a>
  <a href="https://coverage-badge.samuelcolvin.workers.dev/redirect/te25son/Swole-V2" target="_blank">
    <img src="https://coverage-badge.samuelcolvin.workers.dev/te25son/Swole-V2.svg" alt="Coverage">
  </a>
  <a href="https://opensource.org/licenses/Apache-2.0">
    <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License">
  </a>
</div>

### Setup

You will need to install four dependencies in order to run the project locally.

1. [poetry](https://python-poetry.org/docs/#installation)
2. [pre-commit](https://pre-commit.com/#installation)
3. [just](https://github.com/casey/just#packages)
4. [edgedb](https://www.edgedb.com/install)

Once installed, clone this repo with `git clone git@github.com:te25son/Swole-V2.git` and navigate your way into the project's root folder `cd Swole-V2`.

Setup the environment by running `just setup`, and then activate the virtual environment with `poetry shell`.

You should now be able to run all the commands available within the project. Try it out by opening the development database's UI with `just open-dev-ui`, running the local development server with `just run`, or running the tests with `just test`.

If you need help with the commands available via just, run `just help`.
