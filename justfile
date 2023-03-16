default: fix-all

locations := "./src ./tests ./cli"

alias t := test
alias f := fix
alias c := check
alias h := help
alias p := pre-commit-all
alias fa := fix-all
alias ca := check-all

# Show all available recipes
help:
    @just --list

# Setup the project
setup:
    poetry install
    pre-commit install
    poetry run db dev init
    poetry run db dev make-migration
    poetry run db dev migrate
    poetry run db dev seed
    poetry run db test init
    poetry run db test make-migration
    poetry run db test migrate
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
