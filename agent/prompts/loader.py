"""Load versioned Markdown prompts with YAML front matter."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import frontmatter

PROMPTS_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Prompt:
    """A loaded prompt document."""

    name: str
    version: str
    description: str
    body: str
    variables: tuple[str, ...] = ()

    def render(self, **kwargs: Any) -> str:
        missing = [name for name in self.variables if name not in kwargs]
        if missing:
            raise ValueError(
                f"Prompt '{self.name}' v{self.version} missing variables: "
                f"{', '.join(missing)}"
            )
        if not self.variables:
            return self.body
        return self.body.format(**{key: kwargs[key] for key in self.variables})


def load_prompt(
    name: str,
    version: str,
    *,
    variables: dict[str, Any] | None = None,
) -> str:
    """Load a prompt by name and version, optionally rendering declared variables."""
    prompt = get_prompt(name, version)
    if variables is None:
        if prompt.variables:
            raise ValueError(
                f"Prompt '{name}' v{version} requires variables: "
                f"{', '.join(prompt.variables)}"
            )
        return prompt.body
    return prompt.render(**variables)


@lru_cache(maxsize=64)
def get_prompt(name: str, version: str) -> Prompt:
    """Return a cached Prompt object for name + version."""
    path = _prompt_path(name, version)
    if not path.is_file():
        raise FileNotFoundError(
            f"Prompt not found: name={name!r} version={version!r} (expected {path})"
        )

    post = frontmatter.load(path)
    meta_name = str(post.get("name") or "").strip()
    meta_version = str(post.get("version") or "").strip()

    if meta_name and meta_name != name:
        raise ValueError(
            f"Prompt file {path} front matter name {meta_name!r} "
            f"does not match {name!r}"
        )
    if meta_version and meta_version != version:
        raise ValueError(
            f"Prompt file {path} front matter version {meta_version!r} "
            f"does not match {version!r}"
        )

    declared = post.get("variables") or []
    if not isinstance(declared, list):
        raise ValueError(f"Prompt '{name}' v{version}: 'variables' must be a list")

    return Prompt(
        name=name,
        version=version,
        description=str(post.get("description") or "").strip(),
        body=str(post.content).strip() + "\n",
        variables=tuple(str(item) for item in declared),
    )


def _prompt_path(name: str, version: str) -> Path:
    return PROMPTS_DIR / name / f"{version}.md"
