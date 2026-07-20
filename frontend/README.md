# Sarjy Frontend

Minimal browser client for Sarjy. Collects an optional `username`, requests a LiveKit token from the backend, then connects to LiveKit over WebRTC so the user can talk to the agent.

Does **not** call memory, weather, or agent tools — those run server-side. The UI only talks to the FastAPI token endpoint and LiveKit Cloud.

```text
Browser ── POST /livekit/token──► Backend
Browser ── WebRTC audio ─────────► LiveKit Cloud ──► Agent
```

## Layout

```text
frontend/
  index.html      # join form + status
  app.js          # token fetch, Room connect, mic, audio playback
  styles.css
  vite.config.js
  nginx.conf      # Compose/production static serving
  Dockerfile
  package.json
```

## Setup

Prerequisites: Node.js 20+, npm. Backend must be reachable (default `http://localhost:8000`); LiveKit credentials are only needed on the backend/agent.

```bash
# from repo root — full stack
make up
# → http://localhost:3000

# Or local Vite (API via Compose or make api)
make frontend
# → http://localhost:3000  (FRONTEND_PORT=3001 to override)
```

```bash
cd frontend
npm ci
npm run dev      # Vite on :3000
npm run build    # production assets → dist/
```

## Configuration

No build-time env file. API base URL is resolved at runtime:

```js
const API_BASE = window.SARJY_API_BASE || "http://localhost:8000";
```

Compose maps the built app to <http://localhost:3000> (Nginx on port 80 inside the container).

## User Flow

1. Open the UI; restore `username` from `localStorage` if present.
2. **Start** button → `POST {API_BASE}/livekit/token` with optional `username`.
3. Persist returned `username`, connect to LiveKit (`url` + `token`), enable microphone.
4. Speak; agent audio plays via subscribed tracks. **Disconnect** leaves the room.
