"""Topic trend detection via journal embedding clustering."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import structlog

from graceful import graceful_context

logger = structlog.get_logger()


def _kmeans(
    data: np.ndarray, n_clusters: int, n_init: int = 10, max_iter: int = 300, seed: int = 42
) -> np.ndarray:
    """Lightweight KMeans using numpy only (Lloyd's algorithm, multi-init).

    Returns an int array of cluster labels with shape (n_samples,).
    """
    rng = np.random.RandomState(seed)
    n_samples, n_features = data.shape
    best_labels = np.zeros(n_samples, dtype=int)
    best_inertia = np.inf

    for _ in range(n_init):
        # Random initialization (Forgy)
        indices = rng.choice(n_samples, size=n_clusters, replace=False)
        centroids = data[indices].copy()

        for _ in range(max_iter):
            # Assign each point to nearest centroid
            diffs = data[:, np.newaxis, :] - centroids[np.newaxis, :, :]
            dists = np.sum(diffs**2, axis=2)
            labels = np.argmin(dists, axis=1)

            # Update centroids
            new_centroids = np.empty_like(centroids)
            for k in range(n_clusters):
                members = data[labels == k]
                if len(members) == 0:
                    new_centroids[k] = data[rng.randint(n_samples)]
                else:
                    new_centroids[k] = members.mean(axis=0)

            if np.allclose(centroids, new_centroids):
                break
            centroids = new_centroids

        inertia = sum(np.sum((data[labels == k] - centroids[k]) ** 2) for k in range(n_clusters))
        if inertia < best_inertia:
            best_inertia = inertia
            best_labels = labels.copy()

    return best_labels


class TrendDetector:
    """Detect emerging/declining topics from journal embeddings over time."""

    def __init__(self, journal_search, llm_caller=None):
        """
        Args:
            journal_search: JournalSearch instance with embeddings access
            llm_caller: Optional callable(system, prompt, max_tokens) for cluster labeling
        """
        self.search = journal_search
        self.llm_caller = llm_caller

    def detect_trends(
        self,
        days: int = 90,
        window: str = "weekly",
        n_clusters: int = 8,
    ) -> list[dict]:
        """Detect topic trends over time windows.

        Args:
            days: Lookback period
            window: "weekly" or "monthly"
            n_clusters: Number of topic clusters

        Returns:
            List of trend dicts with topic, direction, growth_rate, counts
        """
        entries = self._get_entries_with_timestamps(days)
        if len(entries) < n_clusters:
            return []

        # Bucket entries into time windows
        buckets = self._bucket_entries(entries, window)
        if len(buckets) < 2:
            return []

        # Cluster all entries
        embeddings = np.array([e["embedding"] for e in entries])
        n_clusters = min(n_clusters, len(entries))
        labels = _kmeans(embeddings, n_clusters=n_clusters, n_init=10, seed=42)

        # Assign cluster labels to entries
        for i, entry in enumerate(entries):
            entry["cluster"] = int(labels[i])

        # Track cluster sizes per window
        window_keys = sorted(buckets.keys())
        cluster_counts = defaultdict(lambda: defaultdict(int))
        for entry in entries:
            bucket_key = self._get_bucket_key(entry["created_dt"], window)
            cluster_counts[bucket_key][entry["cluster"]] += 1

        # Calculate growth rates
        trends = []
        for cluster_id in range(n_clusters):
            counts = [cluster_counts[k].get(cluster_id, 0) for k in window_keys]

            # Need at least 2 windows with data
            if sum(1 for c in counts if c > 0) < 2:
                continue

            growth_rate = self._calc_growth_rate(counts)
            representative = self._get_representative_entries(entries, cluster_id, 3)
            label = self._label_cluster(representative)

            trends.append(
                {
                    "topic": label,
                    "cluster_id": cluster_id,
                    "direction": "emerging"
                    if growth_rate > 0.2
                    else "declining"
                    if growth_rate < -0.2
                    else "stable",
                    "growth_rate": round(growth_rate, 3),
                    "counts": counts,
                    "windows": window_keys,
                    "total_entries": sum(counts),
                    "representative_titles": [e.get("title", "") for e in representative],
                }
            )

        return sorted(trends, key=lambda t: abs(t["growth_rate"]), reverse=True)

    def get_emerging_topics(self, threshold: float = 0.2, **kwargs) -> list[dict]:
        """Get topics growing faster than threshold."""
        trends = self.detect_trends(**kwargs)
        return [t for t in trends if t["growth_rate"] > threshold]

    def get_declining_topics(self, threshold: float = 0.2, **kwargs) -> list[dict]:
        """Get topics shrinking faster than threshold."""
        trends = self.detect_trends(**kwargs)
        return [t for t in trends if t["growth_rate"] < -threshold]

    def summarize_trends(self, days: int = 90) -> str:
        """Generate LLM summary of detected trends."""
        trends = self.detect_trends(days=days)
        if not trends:
            return "Not enough journal entries to detect trends."

        if not self.llm_caller:
            return self._format_trends_text(trends)

        trend_text = self._format_trends_text(trends)
        prompt = f"""Analyze these journal topic trends and provide a brief summary:

{trend_text}

Summarize:
1. What topics are gaining attention
2. What topics are fading
3. Any notable patterns or recommendations"""

        with graceful_context("graceful.trends.llm_analysis"):
            return self.llm_caller(
                "You are a personal advisor analyzing journal topic trends.",
                prompt,
                1000,
            )
        return trend_text

    def _get_entries_with_timestamps(self, days: int) -> list[dict]:
        """Get journal entries with embeddings and timestamps."""
        cutoff = datetime.now() - timedelta(days=days)
        entries = self.search.storage.list_entries(limit=500)

        result = []
        for entry in entries:
            try:
                created = entry.get("created")
                if not created:
                    continue
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if dt.tzinfo:
                    dt = dt.replace(tzinfo=None)
                if dt < cutoff:
                    continue

                # Get embedding from ChromaDB
                embedding = self._get_embedding(entry)
                if embedding is None:
                    continue

                result.append(
                    {
                        "path": entry.get("path"),
                        "title": entry.get("title", ""),
                        "type": entry.get("type", ""),
                        "created": created,
                        "created_dt": dt,
                        "tags": entry.get("tags", []),
                        "embedding": embedding,
                    }
                )
            except (ValueError, OSError):
                continue

        return result

    def _get_embedding(self, entry) -> Optional[np.ndarray]:
        """Get embedding vector for an entry from ChromaDB."""
        if not self.search.embeddings:
            return None
        with graceful_context("graceful.trends.embedding_lookup"):
            path_str = str(entry.get("path", ""))
            result = self.search.embeddings.collection.get(
                ids=[path_str],
                include=["embeddings"],
            )
            if result["embeddings"] and result["embeddings"][0]:
                return np.array(result["embeddings"][0])
        return None

    def _bucket_entries(self, entries: list, window: str) -> dict[str, list]:
        """Group entries into time windows."""
        buckets = defaultdict(list)
        for entry in entries:
            key = self._get_bucket_key(entry["created_dt"], window)
            buckets[key].append(entry)
        return dict(buckets)

    @staticmethod
    def _get_bucket_key(dt: datetime, window: str) -> str:
        """Get bucket key for a datetime."""
        if window == "monthly":
            return dt.strftime("%Y-%m")
        # weekly: ISO week
        return f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"

    @staticmethod
    def _calc_growth_rate(counts: list[int]) -> float:
        """Calculate growth rate from a series of counts.

        Uses simple linear regression slope normalized by mean.
        """
        if not counts or all(c == 0 for c in counts):
            return 0.0
        n = len(counts)
        x = np.arange(n, dtype=float)
        y = np.array(counts, dtype=float)
        mean_y = y.mean()
        if mean_y == 0:
            return 0.0
        slope = np.polyfit(x, y, 1)[0]
        return float(slope / mean_y)

    @staticmethod
    def _get_representative_entries(entries: list, cluster_id: int, n: int) -> list[dict]:
        """Get n representative entries from a cluster."""
        cluster_entries = [e for e in entries if e.get("cluster") == cluster_id]
        return cluster_entries[:n]

    def _label_cluster(self, representative: list[dict]) -> str:
        """Generate a label for a cluster from representative entries."""
        titles = [e.get("title", "") for e in representative if e.get("title")]
        tags = []
        for e in representative:
            tags.extend(e.get("tags", []))

        if tags:
            # Most common tag
            from collections import Counter

            common = Counter(tags).most_common(1)
            if common:
                return common[0][0]

        if titles:
            return titles[0][:50]

        return "Topic cluster"

    @staticmethod
    def _format_trends_text(trends: list[dict]) -> str:
        """Format trends as readable text."""
        lines = []
        for t in trends:
            indicator = {"emerging": "+", "declining": "-", "stable": "="}[t["direction"]]
            lines.append(
                f"[{indicator}] {t['topic']} ({t['direction']}, "
                f"growth={t['growth_rate']:+.1%}, entries={t['total_entries']})"
            )
        return "\n".join(lines) if lines else "No trends detected."
