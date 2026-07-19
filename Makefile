.PHONY: up down api agent frontend test install migrate lint format

PORT ?= 8000
FRONTEND_PORT ?= 3000

up:
	docker compose up -d --build

down:
	docker compose down

install:
	cd backend && uv sync --all-groups
	cd agent && uv sync --all-groups
	cd frontend && npm ci

migrate:
	cd backend && uv run alembic upgrade head

api:
	cd backend && uv sync --all-groups && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $(PORT)

agent:
	cd agent && uv sync --all-groups && uv run python agent.py dev

frontend:
	cd frontend && npm ci && npm run dev -- --port $(FRONTEND_PORT)

test:
	cd backend && uv sync --all-groups && uv run pytest -q
	cd agent && uv sync --all-groups && uv run pytest -q

format:
	cd backend && uv sync --all-groups && uv run ruff format .
	cd agent && uv sync --all-groups && uv run ruff format .

lint:
	cd backend && uv sync --all-groups && uv run ruff check .
	cd agent && uv sync --all-groups && uv run ruff check .
