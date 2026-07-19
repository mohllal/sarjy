# Sarjy backend

FastAPI server for the Sarjy voice assistant.

## Layout

```text
app/
  main.py           # app factory + lifespan
  settings.py       # pydantic-settings
  containers.py     # DI container
  db/               # engine, session factory, Base
  uow/              # Unit of Work
  models/           # ORM models (memories, conversation_messages)
  schemas/          # Pydantic response/request models
  services/         # business logic
  routes/           # HTTP routers (one module per file)
alembic/            # DB migrations
```

## APIs

API documentation is available at <http://localhost:8000/docs>.

### LiveKit API

| Method   | Path                                 | Purpose                            |
|----------|--------------------------------------|------------------------------------|
| `POST`   | `/livekit/token`                     | Create a LiveKit token             |

### Persistence APIs

Memories and conversation history are keyed by `username`.

| Method   | Path                                 | Purpose                            |
|----------|--------------------------------------|------------------------------------|
| `PUT`    | `/memories/{username}`               | Upsert one or more key/value facts |
| `GET`    | `/memories/{username}`               | List all facts for username        |
| `DELETE` | `/memories/{username}`               | Clear all facts for username       |
| `POST`   | `/conversations/{username}/messages` | Append turn(s)                     |
| `GET`    | `/conversations/{username}/messages` | Recent history (`limit`/`offset`)  |
| `DELETE` | `/conversations/{username}`          | Clear history                      |

### Health APIs

| Path          | Purpose                                        |
|---------------|------------------------------------------------|
| `GET /health` | Check if the server is running                 |
| `GET /ready`  | Check if the server is ready to serve requests |

## Migrations

```bash
# from repo root
make migrate
```

Compose backend entrypoint runs `alembic upgrade head` before uvicorn.

## Run

Via Compose (recommended for the full stack):

```bash
# from repo root
make up
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Local reload (Postgres still via Compose):

```bash
make api
# or: make api PORT=8001
```
