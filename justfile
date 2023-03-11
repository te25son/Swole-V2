default: fix

locations := "./src ./tests ./cli"

test:
    pytest -n 2 --cov --random-order

fix: (lint) (format) (type)
check: (lint "true") (format "true") (type)

lint check="false":
    ruff {{locations}} {{ if lowercase(check) == "true" { "--exit-non-zero-on-fix" } else { "" } }}

format check="false":
    black {{locations}} {{ if lowercase(check) == "true" { "--check" } else { "" } }}

type:
    mypy {{locations}}
