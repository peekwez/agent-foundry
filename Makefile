OPTION := mortgage
TASK_FILE := src/samples/mortgage/_task.yaml
ENV_FILE := $$(pwd)/.env
REVISIONS := 3

.PHONY: sync run format lint mypy tests coverage run link-path link-data test-context

hooks:
	uv run pre-commit install
	uv run pre-commit autoupdate
	uv run pre-commit install --install-hooks

sync:
	uv sync --all-extras --all-packages --group dev

format:
	uv run ruff format
	uv run ruff check --fix

lint:
	uv run ruff check

mypy:
	uv run mypy .

tests:
	uv run pytest

coverage:
	uv run coverage run -m pytest
	uv run coverage xml -o coverage.xml
	uv run coverage report -m

run:
	cd src && uv run -m main

link-path:
	mkdir -p /tmp/genai/data || true
	mkdir -p /tmp/genai/cache || true

link-data: link-path
	rm -rf /tmp/genai/data/mortgage || true
	cp -r $(shell pwd)/samples/mortgage /tmp/genai/data/mortgage

	rm -rf /tmp/genai/data/research || true
	cp -r $(shell pwd)/samples/research /tmp/genai/data/research

	ls -l /tmp/genai/data

test-run:
	cd src && uv run -m \
		cmd test-task -o ${OPTION}

task-run:
	cd src && uv run -m \
		cmd run-task \
		-c ${TASK_FILE} \
		-e ${ENV_FILE} \
		-r ${REVISIONS}

install-playwright:
	npm install -g playwright
