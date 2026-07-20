# Sarjy Backend

FastAPI service that mints LiveKit room tokens and persists cross-session memory and conversation history.

Does **not** handle WebRTC media, STT/LLM/TTS, or weather — those live in LiveKit Cloud and the agent worker.

```text
Browser ── POST /livekit/token ──► Backend ──► LiveKit Cloud (JWT)
Agent   ── memories / conversations ──► Backend ──► Postgres
```

## Layout

```text
app/
  main.py           # app factory + lifespan
  settings.py       # pydantic-settings
  containers.py     # DI container
  db/               # engine, session factory, Base
  uow/              # Unit of Work
  models/           # ORM (memories, conversation_messages)
  schemas/          # request/response models
  services/         # business logic
  routes/           # HTTP routers
alembic/            # migrations
tests/
```

## Setup

Prerequisites: Python 3.11+, [uv](https://docs.astral.sh/uv/) or Docker and Docker Compose, Postgres (Compose recommended), LiveKit Cloud credentials in the repo-root `.env`.

```bash
# from repo root
cp .env.example .env   # fill LIVEKIT_* values

# Full stack
make up

# Or API alone (Postgres via Compose)
docker compose up -d postgres
make migrate
make api                # http://localhost:8000

# Run tests
cd backend && uv run pytest -q
```

Swagger docs: <http://localhost:8000/docs>

## Configuration

Settings load from repo-root `.env` (or `backend/.env`). Relevant variables:

| Variable                                 | Purpose                         | Default / notes                            |
|------------------------------------------|---------------------------------|--------------------------------------------|
| `DATABASE_URL`                           | Async Postgres URL              | default already provided in `.env.example` |
| `LIVEKIT_URL`                            | LiveKit Cloud WebSocket URL     | required                                   |
| `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` | Token signing                   | required                                   |
| `LIVEKIT_AGENT_NAME`                     | Agent name embedded in dispatch | `sarjy`                                    |
| `CORS_ORIGINS`                           | Comma-separated browser origins | `http://localhost:3000,...`                |
| `APP_ENV`                                | Environment label               | `development`                              |

In Compose, `DATABASE_URL` is overridden to reach the `postgres` service.

## APIs

### LiveKit

| Method | Path             | Purpose                                                            |
|--------|------------------|--------------------------------------------------------------------|
| `POST` | `/livekit/token` | Mint JWT; body may include optional `username` (blank → `guest-…`) |

### Persistence (`username`-scoped)

| Method   | Path                                 | Purpose                             |
|----------|--------------------------------------|-------------------------------------|
| `PUT`    | `/memories/{username}`               | Upsert key/value facts              |
| `GET`    | `/memories/{username}`               | List facts                          |
| `DELETE` | `/memories/{username}`               | Clear facts                         |
| `POST`   | `/conversations/{username}/messages` | Append turn(s)                      |
| `GET`    | `/conversations/{username}/messages` | Recent history (`limit` / `offset`) |
| `DELETE` | `/conversations/{username}`          | Clear history                       |

### Health

| Path          | Purpose                   |
|---------------|---------------------------|
| `GET /health` | Process up                |
| `GET /ready`  | Ready to serve (incl. DB) |
