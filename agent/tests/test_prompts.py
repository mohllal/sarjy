"""Tests for Markdown prompt loading (generic loader behavior)."""

from __future__ import annotations

import pytest

from prompts import get_prompt, load_prompt


def test_load_system_prompt() -> None:
    text = load_prompt("system", "1.0.0")
    assert "Sarjy" in text
    assert "---" not in text


def test_get_prompt_metadata() -> None:
    prompt = get_prompt("system", "1.0.0")
    assert prompt.name == "system"
    assert prompt.version == "1.0.0"
    assert prompt.description


def test_missing_prompt_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        get_prompt("greeting", "9.9.9")
