default: clean check

locations := "./src ./tests ./cli"

test:
    pytest -n 2 --cov

clean:
    black {{locations}}
    ruff {{locations}}

check:
    mypy {{locations}}
