import { Room, RoomEvent, Track } from "livekit-client";

const API_BASE = window.SARJY_API_BASE || "http://localhost:8000";
const USERNAME_KEY = "sarjy_username";

const form = document.getElementById("join-form");
const usernameInput = document.getElementById("username");
const startBtn = document.getElementById("start-btn");
const statusEl = document.getElementById("status");
const identityEl = document.getElementById("identity");

let room = null;

const savedUsername = localStorage.getItem(USERNAME_KEY);
if (savedUsername) {
  usernameInput.value = savedUsername;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (room) {
    await disconnect();
    setStatus("ready", "Ready");
    startBtn.textContent = "Start";
    startBtn.disabled = false;
    return;
  }
  await connect();
});

async function connect() {
  setStatus("connecting", "Connecting…");
  startBtn.disabled = true;

  try {
    const requestedUsername = usernameInput.value.trim();
    const session = await fetchToken(requestedUsername || null);

    localStorage.setItem(USERNAME_KEY, session.username);
    usernameInput.value = session.username;
    identityEl.hidden = false;
    identityEl.textContent =
      `Signed in as ${session.username} · room ${session.room_name}`;

    room = new Room({
      adaptiveStream: true,
      dynacast: true,
    });

    room
      .on(RoomEvent.TrackSubscribed, handleTrackSubscribed)
      .on(RoomEvent.Disconnected, () => {
        setStatus("ready", "Disconnected");
        startBtn.disabled = false;
        startBtn.textContent = "Start";
      })
      .on(RoomEvent.MediaDevicesError, (error) => {
        setStatus("error", `Media error: ${error.message || error}`);
      });

    await room.connect(session.url, session.token);
    await room.localParticipant.setMicrophoneEnabled(true);

    setStatus("connected", "Connected — speak whenever you’re ready");
    startBtn.textContent = "Disconnect";
    startBtn.disabled = false;
  } catch (error) {
    console.error(error);
    setStatus("error", error.message || String(error));
    startBtn.disabled = false;
    startBtn.textContent = "Start";
    await disconnect();
  }
}

async function disconnect() {
  if (!room) {
    return;
  }
  const current = room;
  room = null;
  await current.disconnect();
}

async function fetchToken(username) {
  const response = await fetch(`${API_BASE}/livekit/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username }),
  });

  if (!response.ok) {
    let detail = `Token request failed (${response.status})`;
    try {
      const payload = await response.json();
      if (payload.detail) {
        detail =
          typeof payload.detail === "string"
            ? payload.detail
            : JSON.stringify(payload.detail);
      }
    } catch {
      // ignore parse errors :shrug:
    }
    throw new Error(detail);
  }

  return response.json();
}

function handleTrackSubscribed(track) {
  if (track.kind !== Track.Kind.Audio) {
    return;
  }
  const element = track.attach();
  element.autoplay = true;
  element.playsInline = true;
  document.body.appendChild(element);
}

function setStatus(state, message) {
  statusEl.dataset.state = state;
  statusEl.textContent = message;
}
