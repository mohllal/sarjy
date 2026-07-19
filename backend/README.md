# Sarjy backend

FastAPI server for the Sarjy voice assistant.

## Layout

```text
app/
  main.py           # app factory + lifespan
  config.py         # pydantic-settings
  containers.py     # DI container
  db/               # engine, session factory, Base
  uow/              # Unit of Work
  models/           # ORM models (later)
  schemas/          # Pydantic response/request models
  services/         # business logic
  routes/           # HTTP routers (one module per file)
```

## Run

Via Compose (recommended for the full stack):

```bash
# from repo root
make up
curl http://localhost:8000/health
```

Local reload (Postgres still via Compose):

```bash
make api
# or: make api PORT=8001
```
