# Backend

FastAPI backend for the Proximity app.

## Quick start

1. Create a virtual env and install dependencies with `uv` package manager:

```bash
cd backend
uv venv --python 3.10
source .venv/bin/activate
uv sync --extra dev
```

2. Copy env file:

```bash
cp .env.example .env
```

3. Start Postgres (optional for local dev if using SQLite in tests):

```bash
docker compose up -d
```

4. Run migrations:

```bash
uv run alembic revision --autogenerate -m "initial schema"
uv run alembic upgrade head
```

5. Run API:

```bash
uv run uvicorn app.main:app --reload
```

## Useful commands

- `make dev`
- `make test`
- `make lint`
- `make migrate`
- `make autogen m="message"`
- `make init-db`
