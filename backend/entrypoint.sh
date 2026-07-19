#!/bin/sh
set -eu

echo "Running database migrations..."
.venv/bin/alembic upgrade head

echo "Starting API..."
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
