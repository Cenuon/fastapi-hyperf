# CLAUDE.md

This file provides guidance to Claude Code when working with this codebase.

## Project Overview

Graph is a production-ready FastAPI backend with:
- Async SQLAlchemy 2.0 + PostgreSQL
- Session-based authentication with OAuth (Google/GitHub)
- Unified API response format `{code, message, data}`
- Rate limiting, caching (Redis/Memcached), background tasks (Taskiq)
- Alembic migrations

## Directory Structure

```
app/                    # Main application package
├── api/v1/             # API route handlers (one file per domain)
├── core/               # Infrastructure layer
│   ├── conf/           # Settings, config, enums
│   ├── db/             # SQLAlchemy engine, Base, mixins
│   ├── log/            # Logging configuration
│   ├── auth/           # Auth (OAuth, sessions, password hashing)
│   ├── cache/          # Cache backends (Redis/Memcached)
│   ├── rate_limit/     # Rate limiter core logic
│   └── security/       # Production security validation
├── middleware/          # ASGI middleware
├── models/             # ORM models + CRUD + Pydantic schemas (merged per domain)
├── services/           # Business logic + FastAPI dependencies
├── utils/              # Shared utilities (response, exceptions, error handler)
└── migrations/         # Alembic migration files
task/                   # Taskiq async task workers
config/                 # .env files
scripts/                # Setup/admin scripts
tests/                  # Test suite (unit + integration)
```

## Key Architectural Decisions

### Import Style
- All imports use absolute paths: `from app.core.db.session import Base`
- No relative imports (`from ..xxx`) in app/ directory
- Package root is the project root (where pyproject.toml lives)

### Model Organization
Each domain (user, tier, api_key, rate_limit) has a single file in `app/models/` containing:
- ORM model class
- Pydantic schemas (Read, Create, Update, etc.)
- CRUD instance (`FastCRUD(Model)`)
- Enums (if any)
- Utility functions (if any)

Example: `app/models/user.py` contains `User` model, `UserRead`, `UserCreate`, `crud_users`, `OAuthProvider` enum.

### Service Layer
Business logic lives in `app/services/`. Each service file contains:
- Service class with business methods
- FastAPI dependency factory (`get_xxx_service()`)
- Annotated dependency type (`XxxServiceDep`)

### Unified Response Format
Routes use `create_unified_router()` instead of `APIRouter()`. This automatically wraps responses:
```python
from app.utils.response import create_unified_router

router = create_unified_router(tags=["Users"])
```

Paginated endpoints use `unified_paginated_response()` and `PaginatedData[T]` schema.

### Error Handling
- Domain exceptions in `app/utils/exceptions.py`
- Global error handlers in `app/utils/error_handler.py`
- HTTP exceptions in `app/core/auth/http_exceptions.py`
- All errors return unified format with `support_id` for tracking

## Development Commands

```bash
# Start dev server
uv run fastapi dev app/main.py --port 8005

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/modules/common/test_error_handler.py

# Lint
uv run ruff check app/

# Format
uv run ruff format app/

# Generate migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Create initial data
uv run python scripts/setup_initial_data.py
```

## Environment Configuration

Config file: `config/.env` (copy from `config/.env.example`)

Key settings:
- `POSTGRES_*` - Database connection
- `CACHE_REDIS_*` - Redis for caching (DB 2)
- `RATE_LIMITER_REDIS_*` - Redis for rate limiting (DB 3)
- `TASKIQ_REDIS_*` - Redis for task queue (DB 4)
- `SECRET_KEY` - Session encryption key
- `ENVIRONMENT` - development/staging/production

Settings are loaded in `app/core/conf/settings.py` with env file search path:
1. `/app/config/.env` (Docker)
2. `<project_root>/config/.env` (local development)

## Database

- Engine creation: `app/core/db/session.py`
- Base model: `app/core/db/session.py` (`Base`)
- Mixins: `app/core/db/models.py` (`TimestampMixin`, `SoftDeleteMixin`)
- Migrations: `app/migrations/`
- Alembic config: `alembic.ini`

## Testing

```
tests/
├── conftest.py              # Fixtures, test database setup
├── unit/                    # Unit tests (no external dependencies)
│   └── modules/common/      # Error handler tests
└── integration/             # Integration tests (require database)
    ├── api/v1/users/        # User API tests
    └── auth/                # Auth endpoint tests
```

Run tests: `uv run pytest`

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | Application entry point, creates FastAPI app |
| `app/core/app_factory.py` | `create_application()` factory function |
| `app/core/conf/settings.py` | Pydantic settings, env file loading |
| `app/core/db/session.py` | SQLAlchemy async engine, session factory |
| `app/core/dependencies.py` | Central DI hub (AsyncSessionDep, CurrentUserDep, etc.) |
| `app/utils/response.py` | `UnifiedResponseRoute`, `create_unified_router()` |
| `app/utils/error_handler.py` | Global exception handlers |
| `app/utils/exceptions.py` | Domain exception classes |
| `app/api/v1/__init__.py` | Route aggregation |
