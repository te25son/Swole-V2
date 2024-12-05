# ---------- Base ------------------------------------------------------
FROM python:3.12-slim-bullseye as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    \
    POETRY_VERSION=1.8.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# ---------- Builder ---------------------------------------------------
FROM base as builder

RUN apt-get update \
    && apt-get install --no-install-recommends --assume-yes curl build-essential libffi-dev

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

RUN poetry install --without dev

# ---------- Runtime ---------------------------------------------------
FROM builder as runtime

WORKDIR $PYSETUP_PATH

COPY --from=builder $POETRY_HOME $POETRY_HOME
COPY --from=builder $PYSETUP_PATH $PYSETUP_PATH

RUN poetry install

WORKDIR /app
COPY ./src ./src
COPY ./dbschema ./dbschema
COPY ./edgedb.toml ./edgedb.toml

EXPOSE 8000
CMD [ "uvicorn", "src.swole_v2.main:app", "--reload" ]
