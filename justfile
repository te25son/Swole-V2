default: clean check

locations := "./src ./tests ./cli"

test:
    pytest -n 2 --cov --random-order

clean:
    black {{locations}}
    ruff {{locations}}

check:
    mypy {{locations}}
