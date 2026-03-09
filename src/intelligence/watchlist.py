"""Watchlist matching and follow-up persistence for intelligence items."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

PRIORITY_WEIGHTS = {"high": 3.0, "medium": 2.0, "low": 1.0}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _normalize_key(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _as_list(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        raw_values = value
    else:
        raw_values = [part.strip() for part in value.split(",")]
    result: list[str] = []
    seen: set[str] = set()
    for raw in raw_values:
        cleaned = _normalize_space(str(raw))
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def _priority_value(priority: str | None) -> float:
    return PRIORITY_WEIGHTS.get((priority or "medium").lower(), PRIORITY_WEIGHTS["medium"])


def _make_id(label: str) -> str:
    seed = f"{_normalize_key(label)}|{_utc_now()}"
    return hashlib.sha256(seed.encode()).hexdigest()[:12]


def _sort_items(items: list[dict]) -> list[dict]:
    return sorted(
        items,
        key=lambda item: (
            _priority_value(item.get("priority")),
            item.get("updated_at", ""),
            item.get("label", "").lower(),
        ),
        reverse=True,
    )


def _normalize_item(item: dict) -> dict:
    now = _utc_now()
    label = _normalize_space(item.get("label", ""))
    normalized = {
        "id": item.get("id") or _make_id(label or "watchlist"),
        "label": label,
        "kind": _normalize_space(item.get("kind", "theme") or "theme"),
        "aliases": _as_list(item.get("aliases")),
        "why": _normalize_space(item.get("why", "")),
        "priority": (item.get("priority") or "medium").lower(),
        "tags": _as_list(item.get("tags")),
        "goal": _normalize_space(item.get("goal", "")),
        "time_horizon": _normalize_space(item.get("time_horizon", "quarter") or "quarter"),
        "source_preferences": _as_list(item.get("source_preferences")),
        "created_at": item.get("created_at") or now,
        "updated_at": now,
    }
    return normalized


class WatchlistStore:
    """Path-scoped JSON persistence for watchlist items."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8") or "[]")
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]

    def _save(self, items: list[dict]) -> None:
        self.path.write_text(json.dumps(items, indent=2), encoding="utf-8")

    def list_items(self) -> list[dict]:
        return _sort_items(self._load())

    def save_item(self, item: dict) -> dict:
        normalized = _normalize_item(item)
        items = self._load()
        normalized_label = _normalize_key(normalized["label"])

        replaced = False
        for index, existing in enumerate(items):
            if (
                existing.get("id") == normalized["id"]
                or _normalize_key(existing.get("label", "")) == normalized_label
            ):
                normalized["id"] = existing.get("id") or normalized["id"]
                normalized["created_at"] = existing.get("created_at") or normalized["created_at"]
                items[index] = normalized
                replaced = True
                break

        if not replaced:
            items.append(normalized)

        self._save(_sort_items(items))
        return normalized

    def update_item(self, item_id: str, updates: dict) -> dict | None:
        items = self._load()
        for index, existing in enumerate(items):
            if existing.get("id") != item_id:
                continue
            merged = deepcopy(existing)
            merged.update(updates)
            merged["id"] = existing.get("id")
            merged["created_at"] = existing.get("created_at")
            normalized = _normalize_item(merged)
            normalized["id"] = existing.get("id")
            normalized["created_at"] = existing.get("created_at")
            items[index] = normalized
            self._save(_sort_items(items))
            return normalized
        return None

    def delete_item(self, item_id: str) -> bool:
        items = self._load()
        kept = [item for item in items if item.get("id") != item_id]
        if len(kept) == len(items):
            return False
        self._save(_sort_items(kept))
        return True


class IntelFollowUpStore:
    """Path-scoped JSON persistence for saved / annotated intel items."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, dict]:
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text(encoding="utf-8") or "{}")
        if not isinstance(data, dict):
            return {}
        return {str(key): value for key, value in data.items() if isinstance(value, dict)}

    def _save(self, items: dict[str, dict]) -> None:
        self.path.write_text(json.dumps(items, indent=2), encoding="utf-8")

    def get(self, url: str) -> dict | None:
        return self._load().get(url)

    def list_items(self) -> list[dict]:
        items = list(self._load().values())
        return sorted(items, key=lambda item: item.get("updated_at", ""), reverse=True)

    def upsert(
        self,
        *,
        url: str,
        title: str,
        saved: bool,
        note: str = "",
        watchlist_ids: list[str] | None = None,
    ) -> dict:
        items = self._load()
        existing = items.get(url, {})
        cleaned_note = _normalize_space(note)
        now = _utc_now()

        if not saved and not cleaned_note:
            items.pop(url, None)
            self._save(items)
            return {
                "url": url,
                "title": title,
                "saved": False,
                "note": "",
                "watchlist_ids": watchlist_ids or [],
                "updated_at": now,
            }

        entry = {
            "url": url,
            "title": _normalize_space(title),
            "saved": bool(saved),
            "note": cleaned_note,
            "watchlist_ids": _as_list(watchlist_ids or []),
            "created_at": existing.get("created_at") or now,
            "updated_at": now,
        }
        items[url] = entry
        self._save(items)
        return entry


def _item_text(item: dict) -> str:
    parts = [
        item.get("title", ""),
        item.get("summary", ""),
        item.get("content", "")[:1000],
        item.get("source", ""),
        " ".join(item.get("tags", []) if isinstance(item.get("tags"), list) else []),
    ]
    return " ".join(parts).lower()


def _term_matches(text: str, term: str) -> bool:
    normalized = _normalize_space(term).lower()
    if not normalized:
        return False
    if " " in normalized:
        return normalized in text
    return bool(re.search(rf"\b{re.escape(normalized)}\b", text))


def _candidate_terms(item: dict) -> list[str]:
    return _as_list(
        [item.get("label", ""), *_as_list(item.get("aliases")), *_as_list(item.get("tags"))]
    )


def annotate_items(items: list[dict], watchlist_items: list[dict]) -> list[dict]:
    if not watchlist_items:
        return items

    for item in items:
        text = _item_text(item)
        source_key = (item.get("source") or "").lower()
        matches = []
        for watch in watchlist_items:
            matched_terms = [term for term in _candidate_terms(watch) if _term_matches(text, term)]
            if not matched_terms:
                continue
            score = _priority_value(watch.get("priority")) + min(1.5, len(matched_terms) * 0.4)
            preferred_sources = {
                value.lower() for value in _as_list(watch.get("source_preferences"))
            }
            if preferred_sources and source_key in preferred_sources:
                score += 0.35
            matches.append(
                {
                    "watchlist_id": watch.get("id", ""),
                    "label": watch.get("label", ""),
                    "priority": watch.get("priority", "medium"),
                    "matched_terms": matched_terms[:4],
                    "why": watch.get("why", ""),
                    "score": round(score, 3),
                }
            )

        if matches:
            matches.sort(key=lambda match: match["score"], reverse=True)
            top = matches[0]
            item["watchlist_matches"] = matches[:3]
            item["watchlist_score"] = top["score"]
            if top.get("why"):
                item["why_this_matters"] = top["why"]
            else:
                item["why_this_matters"] = f"Matches your watchlist for {top['label']}" + (
                    f" via {', '.join(top['matched_terms'][:2])}"
                    if top.get("matched_terms")
                    else ""
                )
        else:
            item.pop("watchlist_matches", None)
            item.pop("watchlist_score", None)
            item.pop("why_this_matters", None)

    return items


def attach_follow_up_state(items: list[dict], follow_ups: IntelFollowUpStore) -> list[dict]:
    saved_map = {entry["url"]: entry for entry in follow_ups.list_items() if entry.get("url")}
    for item in items:
        entry = saved_map.get(item.get("url", ""))
        if entry:
            item["follow_up"] = entry
    return items


def sort_ranked_items(items: list[dict]) -> list[dict]:
    return sorted(
        items,
        key=lambda item: (
            1 if item.get("watchlist_matches") else 0,
            float(item.get("watchlist_score") or 0.0),
            float(item.get("relevance_score") or 0.0),
            item.get("published") or item.get("scraped_at") or "",
        ),
        reverse=True,
    )


def find_evidence_for_text(text: str, annotated_items: list[dict], limit: int = 2) -> list[str]:
    haystack = (text or "").lower()
    evidence: list[str] = []
    seen: set[str] = set()
    for item in annotated_items:
        matches = item.get("watchlist_matches") or []
        if not matches:
            continue
        item_text = " ".join(
            [item.get("title", ""), item.get("summary", ""), item.get("why_this_matters", "")]
        ).lower()
        if haystack and not any(
            _term_matches(haystack + " " + item_text, match.get("label", "")) for match in matches
        ):
            continue
        top = matches[0]
        line = f"{top.get('label', 'Watchlist')}: {item.get('title', 'Untitled')}"
        if line not in seen:
            seen.add(line)
            evidence.append(line)
        if len(evidence) >= limit:
            break
    return evidence
