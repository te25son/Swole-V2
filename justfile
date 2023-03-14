default: fix

locations := "./src ./tests ./cli"

alias t := test
alias f := fix
alias c := check

# Show all available recipes
help:
    @just -l

# Run all tests
test:
    pytest -n 2 --cov --random-order

# Run linter and formatter
fix: (lint) (format)

# Run lint, format, and type checks
check: (lint-check) (format-check) (type-check)

_lint args="":
    ruff {{locations}} {{args}}

# Run linter
lint: (_lint)

# Run linter and throw error on fix
lint-check: (_lint "--exit-non-zero-on-fix")

_format args="":
    black {{locations}} {{args}}

# Run formatter
format: (_format)

# Run formatter and throw error on fix
format-check: (_format "--check")

# Run type checker
type-check:
    mypy {{locations}}
