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
	mkdir -p /tmp/genai/data || true
	mkdir -p /tmp/genai/cache || true

link-data: link-path
	unlink /tmp/genai/data/bb-samples || true
	ln -s $(shell pwd)/samples /tmp/genai/data/bb-samples
	ls -l /tmp/genai/data/bb-samples/