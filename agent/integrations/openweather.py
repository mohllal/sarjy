"""OpenWeatherMap client (Current Weather 2.5 + Geocoding + Forecast)."""

from __future__ import annotations

import logging
from typing import Any

from livekit.agents import utils
from livekit.agents.llm import ToolError

logger = logging.getLogger("sarjy.integrations.openweather")

_GEOCODE_URL = "https://api.openweathermap.org/geo/1.0/direct"
_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

_CURRENT_WHEN = frozenset({"", "now", "today", "current", "right now"})


class OpenWeatherClient:
    """Fetches compact weather summaries for spoken replies.

    Uses OpenWeather Geocoding + Current Weather / 5-day Forecast.
    """

    def __init__(self, api_key: str) -> None:
        if not api_key.strip():
            raise ValueError("OpenWeather API key is required")
        self._api_key = api_key.strip()

    async def resolve_location(self, location: str) -> dict[str, Any]:
        """Geocode a city/area into a canonical label plus coordinates."""
        place = location.strip()
        if not place:
            raise ToolError("Please provide a city or location.")
        return await self._geocode(place)

    async def get_weather(
        self,
        location: str,
        when: str | None = None,
    ) -> dict[str, Any]:
        when_key = (when or "now").strip().lower()
        coords = await self.resolve_location(location)

        if when_key in _CURRENT_WHEN:
            return await self._current(coords)
        return await self._forecast(coords, when=when_key)

    async def _geocode(self, location: str) -> dict[str, Any]:
        data = await self._request_json(
            _GEOCODE_URL,
            params={"q": location, "limit": 1, "appid": self._api_key},
            error_message="I couldn't look up that location right now.",
        )
        if not data:
            raise ToolError(
                f"I couldn't find a place called {location}. "
                "Try a city name, optionally with a country."
            )
        hit = data[0]
        name = hit.get("name") or location
        country = hit.get("country") or ""
        state = hit.get("state") or ""
        label_parts = [name]
        if state:
            label_parts.append(state)
        if country:
            label_parts.append(country)
        return {
            "lat": hit["lat"],
            "lon": hit["lon"],
            "label": ", ".join(label_parts),
        }

    async def _current(self, coords: dict[str, Any]) -> dict[str, Any]:
        data = await self._request_json(
            _CURRENT_URL,
            params={
                "lat": coords["lat"],
                "lon": coords["lon"],
                "appid": self._api_key,
                "units": "metric",
            },
            error_message="I couldn't fetch the current weather right now.",
        )
        weather = (data.get("weather") or [{}])[0]
        main = data.get("main") or {}
        wind = data.get("wind") or {}
        rain = data.get("rain") or {}
        return {
            "location": coords["label"],
            "when": "current",
            "temp_c": main.get("temp"),
            "feels_like_c": main.get("feels_like"),
            "conditions": weather.get("description") or "unknown",
            "humidity_pct": main.get("humidity"),
            "wind_mps": wind.get("speed"),
            "precip_mm": rain.get("1h") or rain.get("3h"),
            "precip_chance": None,
        }

    async def _forecast(self, coords: dict[str, Any], *, when: str) -> dict[str, Any]:
        data = await self._request_json(
            _FORECAST_URL,
            params={
                "lat": coords["lat"],
                "lon": coords["lon"],
                "appid": self._api_key,
                "units": "metric",
            },
            error_message="I couldn't fetch the weather forecast right now.",
        )
        slots = data.get("list") or []
        if not slots:
            raise ToolError("No forecast data was returned for that location.")

        chosen = _pick_forecast_slot(slots, when)
        weather = (chosen.get("weather") or [{}])[0]
        main = chosen.get("main") or {}
        wind = chosen.get("wind") or {}
        rain = chosen.get("rain") or {}
        return {
            "location": coords["label"],
            "when": when,
            "forecast_time_utc": chosen.get("dt_txt"),
            "temp_c": main.get("temp"),
            "feels_like_c": main.get("feels_like"),
            "conditions": weather.get("description") or "unknown",
            "humidity_pct": main.get("humidity"),
            "wind_mps": wind.get("speed"),
            "precip_mm": rain.get("3h"),
            "precip_chance": chosen.get("pop"),
        }

    async def _request_json(
        self,
        url: str,
        *,
        params: dict[str, Any],
        error_message: str,
    ) -> Any:
        session = utils.http_context.http_session()
        try:
            async with session.get(url, params=params) as response:
                if response.status == 401:
                    raise ToolError(
                        "Weather service authentication failed. Check OPENWEATHER_API_KEY."
                    )
                if response.status == 404:
                    raise ToolError("I couldn't find weather for that location.")
                if response.status == 429:
                    raise ToolError(
                        "The weather service is rate-limited right now. Try again shortly."
                    )
                if response.status >= 400:
                    body = await response.text()
                    logger.warning(
                        "openweather %s failed status=%s body=%s",
                        url,
                        response.status,
                        body[:200],
                    )
                    raise ToolError(error_message)
                return await response.json()
        except ToolError:
            raise
        except TimeoutError as exc:
            raise ToolError("The weather service timed out. Please try again.") from exc
        except Exception as exc:  # noqa: BLE001
            logger.warning("openweather request error: %s", exc)
            raise ToolError(error_message) from exc


def _pick_forecast_slot(slots: list[dict[str, Any]], when: str) -> dict[str, Any]:
    """Pick a 3-hour forecast slot; prefer midday matches when 'afternoon' etc."""
    keywords = when.lower()
    preferred_hours: set[int] = set()
    if any(token in keywords for token in ("morning", "am")):
        preferred_hours = {6, 9}
    elif any(token in keywords for token in ("afternoon", "noon")):
        preferred_hours = {12, 15}
    elif any(token in keywords for token in ("evening", "night", "tonight")):
        preferred_hours = {18, 21}
    elif "weekend" in keywords or "saturday" in keywords:
        preferred_hours = {12, 15}
    elif "sunday" in keywords:
        preferred_hours = {12, 15}

    if preferred_hours:
        for slot in slots:
            dt_txt = str(slot.get("dt_txt") or "")
            # "2024-07-19 12:00:00"
            try:
                hour = int(dt_txt[11:13])
            except (TypeError, ValueError):
                continue
            if hour in preferred_hours:
                return slot

    return slots[0]
