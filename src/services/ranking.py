"""Shared ranking utilities — Reciprocal Rank Fusion."""

from __future__ import annotations

from typing import Callable


def rrf_fuse(
    result_lists: list[list[dict]],
    weights: list[float],
    key_fn: Callable[[dict], str],
    k: int = 60,
) -> list[dict]:
    """Merge ranked result lists via Reciprocal Rank Fusion.

    Args:
        result_lists: Parallel lists of result dicts (e.g. semantic, keyword).
        weights: Per-list weight. Must be same length as result_lists.
        key_fn: Extracts a dedup key from each item dict.
        k: Smoothing constant (default 60 per standard RRF).

    Returns:
        Merged list sorted by descending RRF score.
    """
    assert len(result_lists) == len(weights), "result_lists and weights must have same length"

    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for result_list, weight in zip(result_lists, weights):
        for rank, item in enumerate(result_list):
            key = key_fn(item) or str(id(item))
            scores[key] = scores.get(key, 0.0) + weight / (k + rank + 1)
            if key not in items:
                items[key] = item

    sorted_keys = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [items[k_] for k_ in sorted_keys]
