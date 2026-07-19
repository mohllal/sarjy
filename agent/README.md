# Sarjy agent worker

LiveKit Agents worker using LiveKit Inference (STT → LLM → TTS).

## Layout

```text
agent/
  agent.py                 # thin LiveKit entrypoint
  settings.py
  schemas/                 # SessionData and future typed state
  integrations/            # BackendApiClient, OpenWeatherClient
  assistants/              # SarjyAssistant + function tools
  session/                 # history load, turn persistence
  prompts/
  tests/
```

## Tools

| Tool                           | Purpose                                    |
|--------------------------------|--------------------------------------------|
| `save_memory`                  | Create new fact via the backend FastAPI    |
| `recall_memories`              | Retrieve all facts via the backend FastAPI |
| `get_weather(location, when?)` | OpenWeather current / near-term forecast   |

Weather uses OpenWeather Geocoding + Current Weather 2.5 / 5-day Forecast (free-tier).

## Memory & history

- On session start: loads the last `CONVERSATION_HISTORY_LIMIT` (default 20) turns into chat context so the assistant can respond / remember to the user's previous messages.
- During the session: persists user/assistant turns via the backend FastAPI.

## Prompts

```text
prompts/
  system/1.2.0.md   # memory + weather (default)
  greeting/1.0.0.md
  greeting_guest/1.0.0.md
```

## Run

```bash
# via Compose (recommended)
make up

# or locally
make agent
```

## Tests

```bash
cd agent && uv run pytest -q
```
