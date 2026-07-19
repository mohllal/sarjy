"""Tests for Markdown prompt loading."""

import pytest

from prompts import get_prompt, load_prompt


def test_load_system_prompt() -> None:
    text = load_prompt("system", "1.0.0")
    assert "Sarjy" in text
    assert "---" not in text


def test_load_greeting_with_variables() -> None:
    text = load_prompt(
        "greeting",
        "1.0.0",
        variables={"username": "kareem"},
    )
    assert "kareem" in text


def test_missing_variable_raises() -> None:
    with pytest.raises(ValueError, match="missing variables"):
        load_prompt("greeting", "1.0.0", variables={})


def test_get_prompt_metadata() -> None:
    prompt = get_prompt("system", "1.0.0")
    assert prompt.name == "system"
    assert prompt.version == "1.0.0"
    assert prompt.description
