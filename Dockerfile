# ---------- Python builder ---------------------------------------------------
FROM python:3.10-slim-bullseye as builder

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends build-essential curl libpq-dev

ENV PYTHONUSERBASE=/opt/venv \
    PATH=/opt/venv/bin:${PATH}

WORKDIR /app
COPY poetry.lock pyproject.toml ./
RUN python -m venv $PYTHONUSERBASE \
    && $PYTHONUSERBASE/bin/pip install poetry==1.2.2 \
    && $PYTHONUSERBASE/bin/poetry config virtualenvs.create false \
    && $PYTHONUSERBASE/bin/poetry install --no-root


# ---------- Runtime ----------------------------------------------------------
FROM python:3.10-slim-bullseye as runtime

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends apt-utils libpq5 postgresql-client \
    && apt-get clean

ENV PYTHONUSERBASE=/opt/venv \
    PATH=/opt/venv/bin:${PATH} \
    PYTHONPATH=${PYTHONPATH}:/app

WORKDIR /app
COPY poetry.lock pyproject.toml app/
