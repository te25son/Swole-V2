.PHONY: test check clean
test:
	@poetry run nox -rs test

check:
	@poetry run nox -rt check

clean:
	@poetry run nox -rt clean

.PHONY: clean/check
clean/check: clean check

.PHONY: run/dev run/test
run/dev:
	@app dev run

.PHONY: dbtest dbdev
dbtest:	
	@db test init && db test seed

dbdev:
	@db dev init && db dev seed
