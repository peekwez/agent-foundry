OPTION := mortgage
TASK_FILE := src/samples/mortgage/_task.yaml
ENV_FILE := src/.env 
REVISIONS := 3

.PHONY: sync run format lint mypy tests coverage run link-path link-data test-context

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
	mkdir -p /tmp/genai/data/mcp-tests || true
	mkdir -p /tmp/genai/cache || true

link-data: link-path
	unlink /tmp/genai/data/mcp-tests/mortgage || true
	ln -s $(shell pwd)/samples/mortgage /tmp/genai/data/mcp-tests/mortgage

	unlink /tmp/genai/data/mcp-tests/research || true
	ln -s $(shell pwd)/samples/research /tmp/genai/data/mcp-tests/research

	ls -l /tmp/genai/data/mcp-tests

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
