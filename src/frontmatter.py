"""Small frontmatter compatibility layer used in tests and local runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class Post:
    """Minimal drop-in replacement for python-frontmatter's Post object."""

    def __init__(self, content: str = "", **metadata: Any):
        self.content = content
        self.metadata: dict[str, Any] = dict(metadata)

    def __getitem__(self, key: str) -> Any:
        return self.metadata[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def __contains__(self, key: object) -> bool:
        return key in self.metadata

    def get(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)

    def keys(self):
        return self.metadata.keys()

    def items(self):
        return self.metadata.items()

    def values(self):
        return self.metadata.values()


def load(path: str | Path) -> Post:
    return loads(Path(path).read_text(encoding="utf-8"))


def loads(text: str) -> Post:
    metadata, content = _split_frontmatter(text)
    post = Post(content)
    post.metadata = metadata
    return post


def dump(post: Post, fd) -> None:
    fd.write(dumps(post))


def dumps(post: Post) -> str:
    if post.metadata:
        frontmatter_text = yaml.safe_dump(
            post.metadata, sort_keys=False, allow_unicode=True, default_flow_style=False
        ).strip()
        return f"---\n{frontmatter_text}\n---\n\n{post.content}"
    return post.content


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return {}, text

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, text

    metadata_text = "\n".join(lines[1:end_index])
    content = "\n".join(lines[end_index + 1 :]).lstrip("\n")
    metadata = yaml.safe_load(metadata_text) or {}
    if not isinstance(metadata, dict):
        metadata = {}
    return metadata, content
