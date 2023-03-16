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
    @just --list

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
fix-all: (lint) (format) (pre-commit-fix)

# Run lint, format, and type checks (no pre-commit)
check: (lint-check) (format-check) (type-check)

# Run all checks (including pre-commit)
check-all: (lint-check) (format-check) (type-check) (pre-commit-check)

_lint *args:
    ruff {{locations}} {{args}}

# Run linter
lint: (_lint)

# Run linter and throw error on fix
lint-check: (_lint "--exit-non-zero-on-fix")

_format *args:
    black {{locations}} {{args}}

# Run formatter
format: (_format)

# Run formatter and throw error on fix
format-check: (_format "--check")

# Run type checker
type-check:
    mypy {{locations}}

_pre-commit +hooks:
    @for hook in {{hooks}}; do \
        pre-commit run $hook --all-files; \
    done;

# Run all pre-commit hooks on all files
pre-commit-all:
    pre-commit run --all-files

# Run misc pre commit checks
pre-commit-check: (_pre-commit "check-toml" "check-yaml" "check-json")

# Runs misc pre commit fixes
pre-commit-fix: (_pre-commit "end-of-file-fixer" "trailing-whitespace")

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
destory-dev-db: (_destroy "$DEV_DB")

# Destroy the test database
destory-test-db: (_destroy "$TEST_DB")
