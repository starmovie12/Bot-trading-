# Makefile (MISSION V11). `make smoke` is the smoke command named in STATE.md.
# Tools run through `python3 -m` (the interpreter that has the dev dependencies).
PY ?= python3

.PHONY: smoke bundle
smoke:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .
	$(PY) -m mypy
	$(PY) -m pytest
	cd pehredaar && test -z "$$(gofmt -l .)" && go vet ./... && go test ./...

bundle:
	$(PY) tools/make_bundle.py
