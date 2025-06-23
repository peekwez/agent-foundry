OPTION := mortgage
TASK_FILE := $$(pwd)/samples/mortgage/_task-new.yaml
ENV_FILE := $$(pwd)/.env.agent
REVISIONS := 3

.PHONY: sync run format lint mypy tests coverage run link-path link-data test-context task-run

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

build:
	docker build -t agent-foundry/python312 .

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

task-run:
	uv run ferros run-task \
		-c ${TASK_FILE} \
		-e ${ENV_FILE} \
		-r ${REVISIONS}

install:
	uv pip install -e .

check:
	docker compose ps

down:
	docker compose down --remove-orphans

up: down
	docker compose up -d

clone-blackboard:
	git submodule add git@github.com:pwc-ca-adv-genai-factory/mcp-blackboard.git
	git submodule update --init --recursive

add-agents:
	uv run ferros add-agent -c config/researcher.yaml.j2 -e .env.agent -s openai
	uv run ferros add-agent -c config/extractor.yaml.j2 -e .env.agent -s openai
	uv run ferros add-agent -c config/analyzer.yaml.j2 -e .env.agent -s openai
	uv run ferros add-agent -c config/writer.yaml.j2 -e .env.agent -s openai
	uv run ferros add-agent -c config/editor.yaml.j2 -e .env.agent -s openai
	uv run ferros add-agent -c config/evaluator.yaml.j2 -e .env.agent -s openai

list-agents:
	uv run ferros list-agents -e .env.agent

init-blackboard:
	docker compose stop blackboard-mcp || true
	docker compose rm -f blackboard-mcp || true
	cd mcp-blackboard && make build
	docker compose up -d blackboard-mcp

init-registry:
	docker compose stop agent-foundry-registry || true
	docker compose rm -f agent-foundry-registry || true
	docker volume rm -f agent-foundry_agent_registry_data || true
	docker compose up -d agent-foundry-registry

init-foundry:
	docker compose stop agent-foundry-api agent-foundry-worker || true
	docker compose rm -f agent-foundry-api agent-foundry-worker || true
	docker volume rm -f agent-foundry_agent_foundry_data || true
	docker compose up -d agent-foundry-api agent-foundry-worker
