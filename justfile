set dotenv-load := true

export SMOKESHOW_AUTH_KEY := env_var_or_default("SMOKESHOW_AUTH_KEY", "")
export DEV_DB := env_var_or_default("EDGEDB_INSTANCE", "")
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

[doc("Show all available recipes")]
help:
    @just --list --list-prefix "···· "

[doc("Setup the project")]
setup:
    poetry install
    pre-commit install
    -@just init-dev-db
    -@just init-test-db
    -@just migrate-dev-db
    -@just migrate-test-db
    -@just seed
    @echo "\nSetup finished. Conisider running 'poetry shell' to activate the virtual environment."

[doc("Run all tests")]
[group("testing")]
test *extra_args:
    pytest -n 4 --cov --random-order {{ extra_args }}

[doc("Run tests and publish coverage report")]
[group("testing")]
publish-test-report:
    pytest -n 2 --cov --random-order --cov-report html
    smokeshow upload htmlcov --auth-key $SMOKESHOW_AUTH_KEY

[doc("Run linter and formatter (only run pre-commit if argument is 'all')")]
[group("code quality")]
fix *arg: (_lint) (_format)
    @if [ '{{ arg }}' = 'all' ]; then \
        just _pre-commit "end-of-file-fixer" "trailing-whitespace" "pretty-format-json" "poetry-lock" "sync_with_poetry"; \
    fi

[doc("Run lint, format, and type checks (only run pre-commit if argument is 'all')")]
[group("code quality")]
check *arg: (_lint "--exit-non-zero-on-fix") (_format "--check") (_type-check)
    @if [ '{{ arg }}' = 'all' ]; then \
        just _pre-commit "check-toml" "check-yaml" "check-json" "poetry-check"; \
    fi

_lint *args:
    ruff check {{ locations }} {{ args }}

_format *args:
    ruff format {{ locations }} {{ args }}

_type-check *args:
    mypy {{ locations }} {{ args }}

_pre-commit +hooks:
    @for hook in {{ hooks }}; do \
        pre-commit run $hook --all-files; \
    done;

[doc("Run all pre-commit hooks on all files")]
[group("code quality")]
pre-commit-all:
    pre-commit run --all-files

[doc("Runs the development environment on given port (defaults to 5000)")]
[group("application")]
run port="5000":
    uvicorn src.swole_v2.main:app --reload --port {{ port }}

[doc("Seeds the development database")]
[group("database")]
seed:
    @poetry run seed

_migrate instance:
    -edgedb --instance {{ instance }} migration create
    edgedb --instance {{ instance }} migrate

[doc("Migrate only the development database")]
[group("database")]
migrate-dev-db: (_migrate "$DEV_DB")

[doc("Migrate only the test database")]
[group("database")]
migrate-test-db: (_migrate "$TEST_DB")

_init instance:
    edgedb instance create {{ instance }}

[doc("Initialize the development database")]
[group("database")]
init-dev-db: (_init "$DEV_DB")

[doc("Initialize the test database")]
[group("database")]
init-test-db: (_init "$TEST_DB")

_open_ui instance:
    edgedb --instance {{ instance }} ui

[doc("Open development database UI")]
[group("database")]
open-dev-ui: (_open_ui "$DEV_DB")

[doc("Open test database UI")]
[group("database")]
open-test-ui: (_open_ui "$TEST_DB")

_destroy instance:
    edgedb instance destroy --instance {{ instance }}

[doc("Destroy the development database")]
[group("database")]
destroy-dev-db: (_destroy "$DEV_DB")

[doc("Destroy the test database")]
[group("database")]
destroy-test-db: (_destroy "$TEST_DB")
