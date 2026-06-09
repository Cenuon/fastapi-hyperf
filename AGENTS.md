# AGENTS.md

## Project

**Fastro** — a batteries-included FastAPI boilerplate (async SQLAlchemy 2.0, Pydantic v2, server-side sessions). This is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) with two packages sharing one root venv.

## Commands

```bash
# Install everything (run from repo root)
uv sync --all-packages --all-extras

# Run backend tests (requires Docker for testcontainers Postgres)
cd backend && uv run pytest

# Run a single test file
cd backend && uv run pytest tests/unit/modules/test_user.py

# Run only unit tests (no Docker needed)
cd backend && uv run pytest tests/unit/

# Run only integration tests (Docker required)
cd backend && uv run pytest tests/integration/

# Lint & format
ruff check --fix
ruff format

# Type check
cd backend && mypy src

# Run all pre-commit hooks
pre-commit run --all-files

# Dev server (no Docker, needs local Postgres + Redis)
cd backend && uv run fastapi dev src/interfaces/main.py

# Background worker
cd backend && uv run taskiq worker infrastructure.taskiq.worker:default_broker

# Migrations
cd backend && uv run alembic revision --autogenerate -m "<msg>" && uv run alembic upgrade head

# Initial data (admin user + default tier)
cd backend && uv run python -m scripts.setup_initial_data

# CLI tool (from repo root)
uv run bp --help
uv run bp deploy generate local      # dev compose
uv run bp deploy generate prod       # prod compose
uv run bp env gen-secret             # generate SECRET_KEY
uv run bp env validate               # audit .env
```

## Architecture

### Workspace layout

```
pyproject.toml           # workspace root (NOT a deployable package)
├── backend/             # deployable FastAPI app
│   ├── src/             #  → interfaces/, infrastructure/, modules/
│   ├── tests/           #  → unit/, integration/
│   ├── migrations/      # Alembic
│   ├── scripts/         # setup_initial_data, create_first_superuser, etc.
│   ├── alembic.ini
│   └── pyproject.toml   # package: fastapi-boilerplate v0.18.0
└── cli/                 # `bp` CLI tool (never ships in prod)
    └── src/cli/
        ├── app.py       # Typer app + plugin discovery
        ├── commands/    # deploy, env sub-commands
        ├── features/    # feature framework + builtins
        └── lib/         # shared helpers
```

### Backend source (`backend/src/`)

Three layers with strict separation:

- **`infrastructure/`** — cross-cutting concerns: config, database, auth, cache, rate limiting, taskiq, middleware, app factory, security. The `dependencies.py` file exports annotated type aliases (e.g. `AsyncSessionDep`, `CurrentUserDep`) used across the app.
- **`interfaces/`** — entrypoints and API wiring: `main.py` (app factory + lifespan), `api/v1/` (router registration), `admin/` (SQLAdmin).
- **`modules/`** — vertical-slice domain modules. Each module is self-contained:
  ```
  modules/user/
  ├── models.py        # SQLAlchemy model
  ├── schemas.py       # Pydantic schemas (Create, Read, Update, Internal)
  ├── crud.py          # FastCRUD instance
  ├── service.py       # Business logic class
  ├── dependencies.py  # FastAPI dependency (Annotated type alias)
  ├── routes.py        # APIRouter with endpoints
  └── enums.py         # Module-specific enums
  ```

### Route registration

Modules expose an `APIRouter`. Routes are registered in `interfaces/api/v1/__init__.py`:
```python
router.include_router(users_router, prefix="/users")
```
All routes live under `/api/v1/<module>`.

### Dependency injection pattern

Use annotated type aliases from `infrastructure/dependencies.py`:
```python
from ...infrastructure.dependencies import AsyncSessionDep, CurrentUserDep

async def my_endpoint(db: AsyncSessionDep, user: CurrentUserDep): ...
```
Module-level dependencies follow the same pattern (e.g. `UserServiceDep` in `modules/user/dependencies.py`).

### App entrypoint

`backend/src/interfaces/main.py` — creates the FastAPI app via `create_application()` factory, adds `SessionMiddleware`, initializes SQLAdmin.

## Key conventions

- **Python ≥3.11**, async-first, fully typed (mypy with `check_untyped_defs = true`)
- **Ruff** for lint/format — line length 128, rules: E, F, I, UP (+ UP006/007/035/039, PLC0415)
- **Pydantic v2** models for all schemas; SQLAlchemy 2.0 mapped columns (`Mapped[type]`)
- **FastCRUD** for all database CRUD operations — never write raw SQL queries in services
- **Server-side sessions** (Redis or memory) with CSRF — no JWT in this codebase
- **Soft delete** via `SoftDeleteMixin` — most queries filter `is_deleted=False`
- **Module exceptions** in `modules/common/exceptions.py` — raise domain exceptions, catch in routes with `handle_exception()`
- All new modules follow the vertical-slice pattern (models → schemas → crud → service → dependencies → routes)

## Testing

- **pytest** with `pytest-asyncio` (mode: `auto`) and `testcontainers[postgres]`
- `ENVIRONMENT=pytest` is set automatically via pytest config
- **conftest.py** provides fixtures: `client` (AsyncClient), `test_db`, `test_user`, `test_superuser`, `auth_client`, `superuser_auth_client`
- Integration tests use real Postgres via Docker (testcontainers) — Docker must be running
- Unit tests under `tests/unit/`, integration under `tests/integration/`
- Redis and session backends are mocked globally in conftest — no live Redis needed for tests
- Test markers: `unit`, `integration`, `slow`, `asyncio`

## Environment

- Config via `backend/.env` (see `.env.example` for full reference)
- Settings loaded by `pydantic-settings` in `infrastructure/config/settings.py`
- Key env vars: `ENVIRONMENT`, `SECRET_KEY`, `POSTGRES_*`, `CACHE_*`, `SESSION_*`, `TASKIQ_*`
- Production docs are hidden by default (`ENABLE_DOCS_IN_PRODUCTION=false`)

## CLI plugins

The `bp` CLI supports two entry-point groups for extension:
- `bp.commands` — third-party Typer sub-apps
- `bp.features` — code generators with manifest

## Common pitfalls

- **Alembic runs from `backend/`** — not the repo root. `cd backend` first.
- **Tests require Docker** — testcontainers spins up Postgres. Without Docker, only `tests/unit/` works.
- **`uv run` from repo root** — the single venv covers both workspace members.
- **Module imports use relative paths** — e.g. `from ...infrastructure.dependencies import ...` (3 dots = 3 levels up from `modules/user/routes.py`).
- **Session backend is `memory` in tests** — autouse fixture patches it. Don't rely on Redis in test code.
- **`isort` first-party is `src`** — ruff config sets `known-first-party = ["src"]` for backend, `["cli"]` for CLI.
