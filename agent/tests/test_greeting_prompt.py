"""Tests for greeting and greeting_guest prompts."""

from __future__ import annotations

import pytest

from prompts import get_prompt, load_prompt


def test_greeting_metadata() -> None:
    prompt = get_prompt("greeting", "1.0.0")
    assert prompt.name == "greeting"
    assert prompt.version == "1.0.0"
    assert prompt.description
    assert prompt.variables == ("username",)


def test_greeting_renders_username() -> None:
    text = load_prompt(
        "greeting",
        "1.0.0",
        variables={"username": "kareem"},
    )
    assert "kareem" in text
    assert "{username}" not in text
    assert "Greet" in text
    assert "---" not in text


def test_greeting_requires_username() -> None:
    with pytest.raises(ValueError, match="missing variables"):
        load_prompt("greeting", "1.0.0", variables={})

    with pytest.raises(ValueError, match="requires variables"):
        load_prompt("greeting", "1.0.0")


def test_greeting_guest_has_no_variables() -> None:
    prompt = get_prompt("greeting_guest", "1.0.0")
    assert prompt.name == "greeting_guest"
    assert prompt.variables == ()

    text = load_prompt("greeting_guest", "1.0.0")
    assert "Greet" in text
    assert "{" not in text
    assert "---" not in text
