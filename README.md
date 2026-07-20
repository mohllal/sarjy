# Sarjy

Sarjy is a web-accessible voice assistant that listens and responds in real time, remembers facts across sessions, answers weather questions with live data, and runs a multistep Weekend Outing Planner workflow.

It is built as three cooperating services — a browser client, a FastAPI backend, and a LiveKit Agents worker — plus Postgres for durable state and LiveKit Cloud for realtime media and model inference.

For a full technical deep dive — components, sequence diagrams, data models, and design rationale — see [architecture.md](architecture.md).

---

## What Sarjy does?

1. Voice conversation: browser ↔ LiveKit ↔ agent STT/LLM/TTS ↔ audio back
2. Cross-session memory: key/value facts in Postgres, keyed by `username`, via agent tools
3. Conversation continuity: recent turns loaded on join, new turns persisted during the call
4. Weather: OpenWeatherMap current / forecast via `get_weather`
5. Weekend Outing Planner: LiveKit `TaskGroup`: location → timing → vibe → weather + proposal

Identity is a single **`username`**. Enter one in the UI, or leave it blank and the backend issues a `guest-…` id stored in `localStorage`. The same username scopes memories, history, and agent session metadata.

---

## Architecture at a glance

1. [frontend/](frontend/): Join UI, mic/audio, LiveKit client, calls only the token API
2. [backend/](backend/): Mint LiveKit JWTs (with agent dispatch), memory + conversation CRUD, health
3. [agent/](agent/): Voice pipeline, tools, outing TaskGroup, prompt loading, history hydrate/persist
4. Postgres: Durable memories and conversation turns
5. LiveKit Cloud: Rooms, agent dispatch, WebRTC, Inference (STT/LLM/TTS)
6. OpenWeather: Conditions for tools and the outing propose step

Public path: browser ↔ backend (token) and browser ↔ LiveKit (media).  
Private path (intended for production): agent ↔ backend (memory / conversations) and agent ↔ OpenWeather.

Component-level setup lives in each package README: [frontend](frontend/README.md) · [backend](backend/README.md) · [agent](agent/README.md).

---

## Repository layout

```text
sarjy/
  architecture.md       # Deep-dive architecture & onboarding guide
  backend/              # FastAPI (+ Dockerfile)
  agent/                # LiveKit worker (assistants, workflows, prompts/)
  frontend/             # Vite + livekit-client (+ Dockerfile)
  docker-compose.yml
  .env.example
  Makefile
```

---

## Prerequisites

- Python 3.11+ and [uv](https://docs.astral.sh/uv/)
- Node.js 20+ / npm
- Docker and Docker Compose
- Accounts / keys (see [`.env.example`](.env.example)):
  - [LiveKit Cloud](https://cloud.livekit.io): `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
  - [OpenWeatherMap](https://openweathermap.org/api): `OPENWEATHER_API_KEY` (free tier is enough; new keys may take a few minutes to activate)

---

## Quick start

1. Create a LiveKit Cloud account and get the API keys.
2. Create an OpenWeatherMap account and get the API key.
3. Copy the `.env.example` file to `.env` and fill in the API keys and run `make up` to build and start the services.

```bash
cp .env.example .env
# Fill LIVEKIT_* and OPENWEATHER_API_KEY

make up
```

Then open [http://localhost:3000](http://localhost:3000) → optional username → Start → allow the microphone → speak.

| Service       | URL                                                    |
|---------------|--------------------------------------------------------|
| Frontend      | <http://localhost:3000>                                |
| API + OpenAPI | <http://localhost:8000> · <http://localhost:8000/docs> |
| Health        | <http://localhost:8000/health>                         |
| Adminer       | <http://localhost:8080>                                |

Try: *"My favorite color is blue"* → refresh → rejoin as the same username → *"What's my favorite color?"*  
Or: *"Plan my weekend"* to enter the outing planner.

---

## Local development

Prefer Compose for Postgres; run API / agent / frontend on the host for fast reload:

```bash
docker compose up -d postgres
make migrate
make api         # FastAPI on :8000
make agent       # LiveKit worker in `dev` mode
make frontend    # Vite on :3000
```

| Target                                      | What it does                                     |
|---------------------------------------------|--------------------------------------------------|
| `make up` / `make down`                     | Build + start / stop the full Compose stack      |
| `make install`                              | Sync backend & agent (incl. dev deps) + `npm ci` |
| `make migrate`                              | Alembic upgrade against Postgres                 |
| `make api` / `make agent` / `make frontend` | Host-side reload processes                       |
| `make test`                                 | Backend + agent tests                            |
| `make lint` / `make format`                 | Ruff check / format                              |

```bash
cd backend && uv run pytest -q
cd agent && uv run pytest -q
```

Configuration is loaded from the repo-root `.env` (see [`.env.example`](.env.example)).

---

## Design highlights

A few decisions that shape the codebase (full rationale in [architecture.md](architecture.md)):

- LiveKit Agents + Inference: voice plumbing, turn-taking, dispatch, and STT/LLM/TTS under one credential set; no self-hosted SFU.
- Memory vs conversation history: structured facts (`memories`) for durable preferences; turn transcripts (`conversation_messages`) for continuity. History preload is capped (`CONVERSATION_HISTORY_LIMIT`, default 20) to control latency and LLM context size.
- LiveKit `TaskGroup` for the outing planner: ordered steps with shared state, corrections, and tool use inside a step; clearer than a monolithic prompt for multistep UX.
- OpenWeather: high-frequency, low-ambiguity external usefulness that also grounds weekend plans in real conditions.
- Thin frontend: web-accessible voice join; product depth lives in the agent and APIs.

---

## Documentation map

| Doc                                      | Audience                                                |
|------------------------------------------|---------------------------------------------------------|
| This README                              | Clone → run → orient                                    |
| [architecture.md](architecture.md)       | Engineers onboarding to system design & agent internals |
| [frontend/README.md](frontend/README.md) | UI package                                              |
| [backend/README.md](backend/README.md)   | API package                                             |
| [agent/README.md](agent/README.md)       | Worker package                                          |

---

## Future improvements / production considerations

These are intentional follow-ups for hardening Sarjy beyond the current demo scope.

### Observability

- Emit OpenTelemetry traces/metrics from the LiveKit agent (and backend) and export them to a system such as [Langfuse](https://langfuse.com/docs/observability/overview) for session, tool, STT/LLM/TTS, and latency visibility.
- Correlate traces with `username` / room id to debug cross-session memory and outing flows.

### Prompt management

- Today prompts are versioned Markdown under `agent/prompts/`. Move them into a dedicated prompt management system (e.g. [Langfuse Prompt Management](https://langfuse.com/docs/prompt-management/overview)) so product can iterate on instructions without redeploying the worker, while linking prompt versions to traces.

### Frontend / UX

The current UI is intentionally minimal. Stronger product UX could include:

- A richer interactive surface that visualizes tool invocations, memory reads/writes, and agent reasoning alongside voice.
- Better conversation management: search, filter, pin, and organize historical sessions beyond a single `username` stream.

### Secure internal APIs

In production, Memory and Conversation endpoints must not be publicly reachable.

- Restrict them to the agent (same cluster / VPC / private network), e.g. via network policy, internal ingress, or a separate internal listener.
- Additionally protect them with an internal shared secret so only authenticated in-cluster callers can read or write user data.
- Keep only token minting (and static frontend hosting, if any) on the public surface — with appropriate auth/rate limits.

The current demo exposes these APIs for local convenience, so treat that as non-production.

### Weather caching

- Cache OpenWeather (and geocoding) responses by location + time window to cut outbound calls, improve latency on repeated queries, and stay within free-tier quotas.
