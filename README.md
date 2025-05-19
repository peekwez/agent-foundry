# Agent Foundry

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)

> **Version 0.1.0**
> Multi‑agent framework for planning, executing, and evaluating complex tasks with a focus on reproducibility and developer ergonomics.

---

## ✨ Key Features

- **Composable Actors** – Planner, Builder, Executor, Manager and more, each isolated in `src/actors/`
- **Prompt‑centric Design** – Actor prompts live in `src/actors/prompts/` and can be edited without touching Python code
- **Typed Domain Models** – Powered by _Pydantic v2_ for safe data interchange (`src/core/models.py`)
- **Environment‑first config** – All runtime knobs live in `src/core/config.py` and load from `.env`
- **`uv` Native** – Dependency resolution & virtual‑env management driven by the lightning‑fast [**uv**](https://github.com/astral-sh/uv) tool
- **Makefile Tasks** – Common workflows like _sync_, _format_, _lint_, _tests_, _coverage_ baked in
- **100% Test Coverage Target** – CI fails if unit coverage < 95 %

---

## 🗂️ Project Layout

```bash
.
├── env-sample.txt
├── LICENSE
├── Makefile
├── notes/
│   └── openai-models.txt
├── pyproject.toml
├── README.md
├── samples/
│   ├── files.json
│   ├── mortgage/
│   │   ├── _task.yaml
│   │   ├── credit_report.pdf
│   │   ├── loe_sample.png
│   │   └── ps_sample.png
│   └── research/
│       ├── _task.yaml
│       ├── first_then.pdf
│       ├── org_chart.png
│       └── us_symbols.csv
├── src/
│   ├── __init__.py
│   ├── actors/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── builder.py
│   │   ├── executors.py
│   │   ├── manager.py
│   │   ├── planner.py
│   │   └── prompts/
│   │       ├── planner.md
│   │       ├── re_planner.md
│   │       └── tasks.md
│   ├── cmd.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── config.yaml.j2
│   │   ├── constants.py
│   │   ├── models.py
│   │   ├── processor.py
│   │   └── utils.py
│   ├── main.py
│   ├── mcps.py
│   ├── tools/
│   │   ├── __init__.py
│   │   └── web_search.py
│   └── version.py
├── tests/
│   └── __init__.py
└── uv.lock
```

> **Note**: `__pycache__/` and `__MACOSX/` artefacts are ignored – they need not be committed.

---

## 🚀 Quick Start

## 🏃 Usage Example

The system is driven by a **goal** and a list of **context artifacts**. At runtime these are published to the [_mcp‑blackboard_](https://github.com/peekwez/mcp-blackboard/tree/main) server, which every actor can query for memory & context. Set the server URL via env var **`MCP_BLACKBOARD_SERVER`** (defaults to `http://localhost:8000/sse`).

### Example goal

> Create a one‑page executive brief on the economic impact of Canada’s 2024‑2025 carbon tax changes. Cite at least three sources.

### Example context list

```text
file:///mnt/shared/data/research/us_symbols.csv
file:///mnt/shared/data/research/org_chart.png
file:///mnt/shared/data/research/first_then.pdf
http://goldfinger.utias.utoronto.ca/dwz/
https://www.youtube.com/watch?v=yYALsys-P_w
```

### Run

```bash
# assume BLACKBOARD_URL already exported
make run GOAL="Create a one-page executive brief on the economic impact of Canada’s 2024-2025 carbon tax changes. Cite at least three sources." \             CONTEXT="abfs://mcp-tests/generic/us_symbols.csv,abfs://mcp-tests/generic/org_chart.png,abfs://mcp-tests/generic/first_then.pdf,http://goldfinger.utias.utoronto.ca/dwz/,https://www.youtube.com/watch?v=yYALsys-P_w"
```

The CLI flags `GOAL` and `CONTEXT` are read by `main.py`, which publishes them to the blackboard and starts the actor workflow.

### 1. Install **uv**

```bash
# Unix & macOS
curl -Ls https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

### 2. Sync the environment

```bash
# Creates a .venv, resolves lockfile, installs runtime + dev deps
make sync          # equivalent to: uv sync --all-extras --all-packages --group dev
```

### 3. Run the application

```bash
make run           # ⇒ cd src && uv run -m main
```

`main.py` will:

1. Load configuration (`core.utils`)
2. Instantiate actors
3. Generate a plan from human input
4. Execute tasks and stream progress
5. Persist results

### 4. Developer Workflow

| Task         | Command         | Description                              |
| ------------ | --------------- | ---------------------------------------- |
| Format code  | `make format`   | Run **ruff** auto‑formatter and fix lint |
| Static check | `make lint`     | Lint with ruff                           |
| Type check   | `make mypy`     | Mypy strict optional                     |
| Run tests    | `make tests`    | Execute **pytest** suite                 |
| Coverage     | `make coverage` | Fail if coverage < 95 %                  |

> All tasks use `uv run` under the hood so they run inside the same virtual env.

---

## 🔌 Configuration

All settings are environment‑driven. Create a `.env` in project root (see `core/models.py` for fields). Example:

```dotenv
# tavily and logfire
TAVILY_API_KEY=
LOGFIRE_WRITE_KEY=

# mcp blackboard server
MCP_BLACKBOARD_SERVER=http://localhost:8000/sse

# provider
MODEL_API_KEY=
MODEL_BASE_URL=https://genai-sharedservice-americas.pwc.com

# context builder agent
CONTEXT_BUILDER_MODEL=openai.o3-2025-04-16
CONTEXT_BUILDER_TEMPERATURE=0
CONTEXT_BUILDER_MAX_TOKENS=4096

# planner agent
PLANNER_MODEL=openai.o3-2025-04-16
PLANNER_TEMPERATURE=0
PLANNER_MAX_TOKENS=4096

# researcher agent
RESEARCHER_MODEL=openai.o3-2025-04-16
RESEARCHER_TEMPERATURE=0
RESEARCHER_MAX_TOKENS=8192

# extractor agent
EXTRACTOR_MODEL=openai.o3-mini-2025-01-31
EXTRACTOR_TEMPERATURE=0
EXTRACTOR_MAX_TOKENS=4096

# analyzer agent
ANALYZER_MODEL=openai.o3-mini-2025-01-31
ANALYZER_TEMPERATURE=0
ANALYZER_MAX_TOKENS=4096

# writer agent
WRITER_MODEL=openai.o1-2024-12-17
WRITER_TEMPERATURE=0.2
WRITER_MAX_TOKENS=16384

# editor agent
EDITOR_MODEL=openai.o1-2024-12-17
EDITOR_TEMPERATURE=0.2
EDITOR_MAX_TOKENS=16384

# evaluator agent
EVALUATOR_MODEL=openai.o3-mini-2025-01-31
EVALUATOR_TEMPERATURE=0
EVALUATOR_MAX_TOKENS=1024
```

---

## 🧩 Extending Agent Foundry

1. **New actor**

   ```bash
   touch src/actors/my_actor.py
   ```

   Inherit from `BaseActor` and register it in `actors/__init__.py`.

2. **Custom prompts**
   Drop a Markdown file in `actors/prompts/` and reference it via the actor’s `prompt_file` attribute.

3. **Integrate external tools / MCPs**
   Extend `mcps.py` with a `{YourTool}MCP` class exposing the desired ops, then inject it where needed.

---

## 🛠️ Dependencies

Runtime:

```toml
[
  "openai-agents>=0.0.12",
  "pydantic>=2.11.3",
  "python-dotenv>=1.1.0",
  "pyyaml>=6.0.2"
]
```

Dev‑only (installed by default via `make sync`):

```toml
[
  "coverage>=7.8.0",
  "ipython>=9.1.0",
  "mypy>=1.15.0",
  "pytest>=8.3.5",
  "pytest-cov>=6.1.1",
  "pytest-mock>=3.14.0",
  "rich>=14.0.0",
  "ruff>=0.11.7"
]
```

> All dependencies are locked in `uv.lock` for deterministic builds.

---

## 📜 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.

---

## 🙏 Acknowledgements

- [Astral‑SH uv](https://github.com/astral-sh/uv) for lightning‑fast dependency management
- [OpenAI Agents SDK](https://github.com/openai/openai-python/tree/main/openai/agents) for the agent runtime
