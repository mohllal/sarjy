# Sarjy agent worker

LiveKit Agents worker using LiveKit Inference (STT → LLM → TTS).

## Layout

```text
agent/
  agent.py                 # thin LiveKit entrypoint
  settings.py
  schemas/                 # SessionData and future typed state
  integrations/            # BackendApiClient (+ OpenWeather later)
  assistants/              # SarjyAssistant + function tools
  session/                 # identity, history load, turn persistence
  prompts/
  tests/
```

## Memory & history

The worker talks to FastAPI for durable facts and conversation turns:

- Tools on `SarjyAssistant`:
  - `save_memory(key, value)`: saves a durable preference or personal fact.
  - `recall_memories()`: full list of memories for the current `username`
- On session start: loads the last `CONVERSATION_HISTORY_LIMIT` turns into the agent chat context
- During the session: persists user/assistant turns via `conversation_item_added`

## Prompts

Versioned Markdown prompts live under `prompts/`:

```text
prompts/
  __init__.py
  loader.py
  system/1.0.0.md
  system/1.1.0.md   # memory tool instructions (default)
  greeting/1.0.0.md
  greeting_guest/1.0.0.md
```

Each Markdown file starts with YAML front matter (`name`, `version`, `description`, optional `variables`). Load them with:

```python
from prompts import load_prompt

instructions = load_prompt("system", "1.1.0")
greeting = load_prompt("greeting", "1.0.0", variables={"username": "kareem"})
```

## Run

```bash
# via Compose (recommended)
make up

# or locally
make agent
```
