# Sarjy agent worker

LiveKit Agents worker using **LiveKit Inference** (STT → LLM → TTS).

Dispatch name comes from `LIVEKIT_AGENT_NAME` in `.env` (must match backend token `RoomAgentDispatch`).

Agent config is loaded via Pydantic Settings in `settings.py` (`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `LIVEKIT_AGENT_NAME`, prompt versions).

## Prompts

Versioned Markdown prompts live under `prompts/`:

```text
prompts/
  __init__.py
  loader.py
  system/1.0.0.md
  greeting/1.0.0.md
  greeting_guest/1.0.0.md
```

Each Markdown file starts with YAML front matter (`name`, `version`, `description`, optional `variables`). Load them with:

```python
from prompts import load_prompt

instructions = load_prompt("system", "1.0.0")
greeting = load_prompt("greeting", "1.0.0", variables={"username": "kareem"})
```

## Run

```bash
# via Compose (recommended)
make up

# or locally
make agent
```
