.PHONY: install test lint run eval format clean

PYTHON ?= python3
VENV ?= .venv
BIN := $(shell if [ -d ".venv/bin" ]; then echo ".venv/bin/"; fi)

install:
	$(BIN)$(PYTHON) -m pip install -e ".[dev]"

test:
	$(BIN)pytest

lint:
	$(BIN)ruff check .
	$(BIN)ruff format --check .

format:
	$(BIN)ruff format .
	$(BIN)ruff check --fix .

run:
	$(BIN)weirdclauses doctor

eval:
	$(BIN)python -m eval.run_eval

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
