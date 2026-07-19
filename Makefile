.PHONY: up down api agent frontend test install

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

api:
	cd backend && uv sync --all-groups && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $(PORT)

agent:
	cd agent && uv sync --all-groups && uv run python agent.py dev

frontend:
	cd frontend && npm ci && npm run dev -- --port $(FRONTEND_PORT)

test:
	cd backend && uv sync --all-groups && uv run pytest -q
	cd agent && uv sync --all-groups && uv run pytest -q
