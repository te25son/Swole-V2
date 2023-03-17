set dotenv-load

export DEV_DB := env_var("EDGEDB_INSTANCE")
export TEST_DB := "test_db"

_default: fix-all

locations := "./src ./tests ./cli"

alias t := test
alias f := fix
alias c := check
alias h := help
alias o := open-dev-ui
alias p := pre-commit-all
alias m := migrate-dev-db
alias fa := fix-all
alias ca := check-all

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

# Run linter and formatter (no pre-commit)
fix: (lint) (format)

# Run all fixes (including pre-commit)
fix-all: (lint) (format) (pre-commit "end-of-file-fixer" "trailing-whitespace")

# Run lint, format, and type checks (no pre-commit)
check: (lint "--exit-non-zero-on-fix") (format "--check") (type-check)

# Run all checks (including pre-commit)
check-all: (lint "--exit-non-zero-on-fix") (format "--check") (type-check) (pre-commit "check-toml" "check-yaml" "check-json")

# Run linter with optional arguments
lint *args:
    ruff {{locations}} {{args}}

# Run formatter with optional arguments
format *args:
    black {{locations}} {{args}}

# Run type checker
type-check:
    mypy {{locations}}

# Run specified pre-commit hooks
pre-commit +hooks:
    @for hook in {{hooks}}; do \
        pre-commit run $hook --all-files; \
    done;

# Run all pre-commit hooks on all files
pre-commit-all:
    pre-commit run --all-files

# Runs the development environment
run:
    uvicorn src.swole_v2.main:app --reload --port 5000

# Seeds the development database
seed:
    @poetry run seed

_migrate instance:
    -edgedb --instance {{instance}} migration create
    edgedb --instance {{instance}} migrate

# Migrate only the development database
migrate-dev-db: (_migrate "$DEV_DB")

# Migrate only the test database
migrate-test-db: (_migrate "$TEST_DB")

_init instance:
    edgedb instance create {{instance}}

# Initialize the development database
init-dev-db: (_init "$DEV_DB")

# Initialize the test database
init-test-db: (_init "$TEST_DB")

_open_ui instance:
    edgedb --instance {{instance}} ui

# Open development database UI
open-dev-ui: (_open_ui "$DEV_DB")

# Open test database UI
open-test-ui: (_open_ui "$TEST_DB")

_destroy instance:
    edgedb instance destroy --instance {{instance}}

# Destroy the development database
destroy-dev-db: (_destroy "$DEV_DB")

# Destroy the test database
destroy-test-db: (_destroy "$TEST_DB")
