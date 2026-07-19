.PHONY: up down api test install

PORT ?= 8000

up:
	docker compose up -d

down:
	docker compose down

install:
	cd backend && uv sync

api: install
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $(PORT)

test:
	@echo "No tests yet — placeholder succeeds."
	@exit 0
