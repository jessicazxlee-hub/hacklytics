.PHONY: install dev test lint migrate autogen init-db

install:
	uv sync --extra dev

dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest -q

lint:
	uv run ruff check .

migrate:
	uv run alembic upgrade head

autogen:
	uv run alembic revision --autogenerate -m "$(m)"

init-db:
	uv run python -m app.db.init_db
