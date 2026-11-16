# Backend API

FastAPI backend for the wind turbine visualization. Conventions: see [`AGENTS.md`](../AGENTS.md).

## Quick start

1. Install [uv](https://docs.astral.sh/uv/) once, then restart VS Code:

   ```bash
   winget install --id=astral-sh.uv -e                  # Windows
   curl -LsSf https://astral.sh/uv/install.sh | sh      # macOS / Linux
   ```

2. From the `backend/` folder:

   ```bash
   uv sync             # like `npm install`
   uv run fastapi dev  # like `npm run dev`
   ```

3. Open http://127.0.0.1:8000/docs

## Commands

| Command | What it does |
|---|---|
| `uv sync` | Install dependencies (run again after pulling) |
| `uv run fastapi dev` | Start dev server with auto-reload |
| `uv run pytest` | Run tests |
| `uv run ruff check .` / `uv run ruff format .` | Lint / format |
| `uv add <pkg>` / `uv add --dev <pkg>` | Add a dependency (commit `uv.lock` too) |

## Structure

```text
src/wind_turbine_visualization/
├── main.py          # creates the app
└── api/routes/      # one file per endpoint group
```

Only `api/` imports FastAPI. Calculations go into plain Python modules.

## Problems?

- `uv` not found: restart VS Code completely.
- Run all commands from `backend/`.
- Import errors in VS Code: *Python: Select Interpreter* → `backend/.venv`.
