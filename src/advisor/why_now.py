"""Rules-based why-now metadata for suggestions and recommendations."""

from __future__ import annotations


class WhyNowReasoner:
    """Attach compact, inspectable evidence chips to surfaced items."""

    def __init__(self, *, max_chips_per_item: int = 3):
        self.max_chips_per_item = max_chips_per_item

    def explain_suggestion(self, suggestion: dict, user_context: dict) -> list[dict]:
        chips: list[dict] = []
        kind = suggestion.get("kind") or ""
        title = f"{suggestion.get('title', '')} {suggestion.get('description', '')}".lower()

        if kind == "stale_goal":
            chips.append(
                {
                    "code": "stale_goal",
                    "label": "Goal needs attention",
                    "severity": "info",
                    "detail": {},
                }
            )

        if any(
            title and label.lower() in title for label in user_context.get("watchlist_labels") or []
        ):
            matches = [
                label
                for label in user_context.get("watchlist_labels") or []
                if label.lower() in title
            ]
            chips.append(
                {
                    "code": "watchlist_match",
                    "label": f"{len(matches)} watchlist match{'es' if len(matches) != 1 else ''}",
                    "severity": "info",
                    "detail": {"watchlist_ids": matches},
                }
            )

        if any(thread.lower() in title for thread in user_context.get("thread_labels") or []):
            chips.append(
                {
                    "code": "thread_reactivated",
                    "label": "Recurring thread active",
                    "severity": "info",
                    "detail": {},
                }
            )

        return chips[: self.max_chips_per_item]

    def explain_recommendation(self, recommendation: dict, user_context: dict) -> list[dict]:
        chips: list[dict] = []
        evidence = recommendation.get("watchlist_evidence") or []
        if evidence:
            chips.append(
                {
                    "code": "watchlist_match",
                    "label": f"{len(evidence)} relevant watchlist match{'es' if len(evidence) != 1 else ''}",
                    "severity": "info",
                    "detail": {"evidence": evidence},
                }
            )

        harvested = recommendation.get("harvested_outcome") or {}
        if harvested.get("state") == "positive":
            chips.append(
                {
                    "code": "executed_similar",
                    "label": "Similar action paid off",
                    "severity": "success",
                    "detail": harvested,
                }
            )

        title = f"{recommendation.get('title', '')} {recommendation.get('description', '')}".lower()
        recent_hits = [
            item
            for item in user_context.get("recent_intel") or []
            if any(term in title for term in str(item.get("title") or "").lower().split()[:6])
        ]
        if recent_hits:
            chips.append(
                {
                    "code": "recent_intel",
                    "label": f"{len(recent_hits)} recent intel signal{'s' if len(recent_hits) != 1 else ''}",
                    "severity": "info",
                    "detail": {
                        "source_urls": [item.get("url") for item in recent_hits if item.get("url")]
                    },
                }
            )

        return chips[: self.max_chips_per_item]
