# FastAPI Hyperf Application

## Features

* Fully async FastAPI + SQLAlchemy 2.0
* Pydantic v2 models & validation
* Unified API response format: `{code, message, data}`
* Server-side sessions + CSRF; OAuth (Google/GitHub)
* Rate limiter with per-tier, per-path rules
* FastCRUD for efficient CRUD & pagination
* Redis or Memcached caching
* [Taskiq](https://taskiq-python.github.io/) workers for async tasks
* Alembic migrations with production safety checks
* Docker multi-stage builds

## Project Structure

```
Graph/
├── app/                        # Application
│   ├── main.py                 # Entry point
│   ├── api/v1/                 # API routes
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── users.py            # User management
│   │   ├── tiers.py            # Tier management
│   │   ├── api_keys.py         # API key management
│   │   └── rate_limits.py      # Rate limit management
│   ├── core/                   # Infrastructure
│   │   ├── conf/               # Configuration & settings
│   │   ├── db/                 # Database (SQLAlchemy engine, Base, mixins)
│   │   ├── log/                # Logging
│   │   ├── auth/               # Auth (OAuth, sessions, password utils)
│   │   ├── cache/              # Caching (Redis/Memcached)
│   │   ├── rate_limit/         # Rate limiting core
│   │   ├── security/           # Production security validation
│   │   ├── app_factory.py      # FastAPI app factory
│   │   ├── dependencies.py     # Central DI hub
│   │   └── middleware.py       # Security headers, client cache
│   ├── middleware/              # Application middleware
│   ├── models/                 # Data models (ORM + CRUD + Schemas)
│   ├── services/               # Business logic
│   ├── utils/                  # Utilities (response, exceptions, error handler)
│   └── migrations/             # Alembic migrations
├── task/                       # Async task workers (Taskiq)
├── config/                     # Environment configuration (.env)
├── scripts/                    # Setup scripts
├── tests/                      # Test suite
├── alembic.ini
├── pyproject.toml
└── Dockerfile
```

## Quickstart

### Prerequisites

* Python 3.11+
* PostgreSQL
* Redis

### Setup

```bash
# Clone and install dependencies
git clone <repo-url>
cd fastapi hyperf
uv sync

# Configure environment
cp config/.env.example config/.env
# Edit config/.env with your database and Redis credentials

# Run migrations
uv run alembic upgrade head

# Create initial data (admin user + default tier)
uv run python scripts/setup_initial_data.py

# Start development server
uv run fastapi dev app/main.py --port 8005
```

API will be available at `http://127.0.0.1:8005`  
Swagger docs at `http://127.0.0.1:8005/docs`

### Start task worker (optional)

```bash
uv run python -m taskiq worker task.worker:default_broker
```

## API Response Format

All API responses follow a unified envelope:

```json
// Success
{
  "code": 200,
  "message": "success",
  "data": { ... }
}

// Paginated
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "size": 10,
    "has_more": false
  }
}

// Error
{
  "code": 404,
  "message": "Resource not found",
  "data": null,
  "support_id": "abc123"
}
```

## Common Tasks

```bash
# Run tests
uv run pytest

# Generate migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Run linter
uv run ruff check app/

# Format code
uv run ruff format app/
```

## Docker

```bash
# Build and run
docker compose up --build

# Or build manually
docker build -t graph-api .
docker run -p 8000:8000 --env-file config/.env graph-api
```

## License

MIT
