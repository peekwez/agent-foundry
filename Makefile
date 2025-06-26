OPTION := mortgage
TASK_FILE := $$(pwd)/samples/mortgage/_task-new.old.yaml
ENV_FILE := $$(pwd)/.env.agent.local
REVISIONS := 1
AGENT_NAMES:= researcher extractor analyzer writer editor

define add-agent-template
	uv run ferros add-agent -c config/$(1).yaml.j2 -e .env.agent.local -s openai
endef

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

link-path:
	mkdir -p /tmp/genai/data || true
	mkdir -p /tmp/genai/cache || true

link-data: link-path
	rm -rf /tmp/genai/data/mortgage || true
	cp -r $(shell pwd)/samples/mortgage /tmp/genai/data/mortgage

	rm -rf /tmp/genai/data/research || true
	cp -r $(shell pwd)/samples/research /tmp/genai/data/research

	ls -l /tmp/genai/data

run:
	uv run ferros run-task \
		-c ${TASK_FILE} \
		-e ${ENV_FILE} \
		-r ${REVISIONS}

api:
	uv run ferros api \
		-e ${ENV_FILE} \
		--host localhost \
		--port 8888

install:
	uv pip install -e .

check:
	docker compose ps

down:
	docker compose down --remove-orphans

up: down
	docker compose --env-file .env.compose up -d

clone-blackboard:
	git submodule add git@github.com:pwc-ca-adv-genai-factory/mcp-blackboard.git
	git submodule update --init --recursive

add-agents:
	for agent in $(AGENT_NAMES); do \
		$(call add-agent-template,$$agent); \
	done

list-agents:
	uv run ferros list-agents -e .env.agent.local

# monitor:
# 	docker compose stop redis minio clickhouse langfuse-worker langfuse-web --env-file .env.compose || true
# 	docker compose rm -f redis minio clickhouse langfuse-worker langfuse-web --env-file .env.compose || true
# 	docker compose up -d redis minio clickhouse langfuse-worker langfuse-web --env-file .env.compose

blackboard:
	docker compose stop blackboard-mcp || true
	docker compose rm -f blackboard-mcp || true
	docker build -t blackboard-mcp/python313 -f mcp-blackboard/Dockerfile mcp-blackboard
	docker compose --env-file .env.compose up -d blackboard-mcp

registry:
	docker compose stop agent-foundry-registry || true
	docker compose rm -f agent-foundry-registry|| true
	docker volume rm -f agent-foundry_agent_registry_data || true
	docker compose --env-file .env.compose up -d agent-foundry-registry

foundry:
	docker compose stop agent-foundry-api agent-foundry-worker || true
	docker compose rm -f agent-foundry-api agent-foundry-worker || true
	docker build -t agent-foundry/python312 .
	docker compose --env-file .env.compose up -d agent-foundry-api agent-foundry-worker
