OPTION := mortgage
TASK_FILE := src/samples/mortgage/_task.yaml
ENV_FILE := src/.env 
REVISIONS := 3

.PHONY: sync run format mypy tests coverage lint all

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
	uv run coverage report -m --fail-under=95

test-run:
	cd src && uv run -m \
		cmd test-task -o ${OPTION}

task-run:
	cd src && uv run -m \
		cmd run-task \
		-c ${TASK_FILE} \
		-e ${ENV_FILE} \
		-r ${REVISIONS}


