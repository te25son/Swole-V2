.PHONY: test check clean
test:
	@poetry run nox -rs test

check:
	@poetry run nox -rt check

clean:
	@poetry run nox -rt clean

.PHONY: clean/check
clean/check: clean check
