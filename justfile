set dotenv-load := true

export DEV_DB := env_var("EDGEDB_INSTANCE")
export TEST_DB := "test_db"

_default:
    just fix "all"
    just check "all"

locations := "./src ./tests ./cli"

[private]
alias t := test
[private]
alias f := fix
[private]
alias c := check
[private]
alias h := help
[private]
alias o := open-dev-ui
[private]
alias p := pre-commit-all
[private]
alias m := migrate-dev-db

# Show all available recipes
help:
    @just --list --list-prefix "···· "

# Setup the project
setup:
    poetry install
    pre-commit install
    -@just init-dev-db
    -@just init-test-db
    -@just migrate-dev-db
    -@just migrate-test-db
    -@just seed
    @echo "\nSetup finished. Conisider running 'poetry shell' to activate the virtual environment."

# Run all tests
test:
    pytest -n 2 --cov --random-order

# Run linter and formatter (only run pre-commit if argument is "all")
fix *arg: (lint) (format)
    @if [ '{{ arg }}' == 'all' ]; then \
        just _pre-commit "end-of-file-fixer" "trailing-whitespace"; \
    fi

# Run lint, format, and type checks (only run pre-commit if argument is "all")
check *arg: (lint "--exit-non-zero-on-fix") (format "--check") (type-check)
    @if [ '{{ arg }}' == 'all' ]; then \
        just _pre-commit "check-toml" "check-yaml" "check-json"; \
    fi

# Run linter on locations with optional arguments
lint *args:
    ruff {{ locations }} {{ args }}

# Run formatter on locations with optional arguments
format *args:
    black {{ locations }} {{ args }}

# Run type checker on locations with optional arguments
type-check *args:
    mypy {{ locations }} {{ args }}

_pre-commit +hooks:
    @for hook in {{ hooks }}; do \
        pre-commit run $hook --all-files; \
    done;

# Run all pre-commit hooks on all files
pre-commit-all:
    pre-commit run --all-files

# Runs the development environment on given port (defaults to 5000)
run port="5000":
    uvicorn src.swole_v2.main:app --reload --port {{ port }}

# Seeds the development database
seed:
    @poetry run seed

_migrate instance:
    -edgedb --instance {{ instance }} migration create
    edgedb --instance {{ instance }} migrate

# Migrate only the development database
migrate-dev-db: (_migrate "$DEV_DB")

# Migrate only the test database
migrate-test-db: (_migrate "$TEST_DB")

_init instance:
    edgedb instance create {{ instance }}

# Initialize the development database
init-dev-db: (_init "$DEV_DB")

# Initialize the test database
init-test-db: (_init "$TEST_DB")

_open_ui instance:
    edgedb --instance {{ instance }} ui

# Open development database UI
open-dev-ui: (_open_ui "$DEV_DB")

# Open test database UI
open-test-ui: (_open_ui "$TEST_DB")

_destroy instance:
    edgedb instance destroy --instance {{ instance }}

# Destroy the development database
destroy-dev-db: (_destroy "$DEV_DB")

# Destroy the test database
destroy-test-db: (_destroy "$TEST_DB")
