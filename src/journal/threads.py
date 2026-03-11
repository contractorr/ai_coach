"""Journal recurrence detection — group related entries into threads via ChromaDB similarity."""

from dataclasses import dataclass, field
from datetime import datetime

import structlog

from .thread_store import ThreadStore

logger = structlog.get_logger()


@dataclass
class ThreadMatch:
    entry_id: str
    thread_id: str | None  # None if unthreaded
    match_type: str  # "joined_existing" | "created_new" | "unthreaded"
    similar_entries: list[str] = field(default_factory=list)
    is_new_thread: bool = False


class ThreadDetector:
    """Detect recurring topics by clustering journal entries via ChromaDB similarity."""

    def __init__(self, journal_embeddings, thread_store: ThreadStore, config: dict | None = None):
        """
        Args:
            journal_embeddings: EmbeddingManager with ChromaDB collection
            thread_store: ThreadStore for persisting thread groupings
            config: dict with similarity_threshold, candidate_count, min_entries_for_thread
        """
        self._embeddings = journal_embeddings
        self._store = thread_store
        cfg = config or {}
        self._similarity_threshold = cfg.get("similarity_threshold", 0.78)
        self._candidate_count = cfg.get("candidate_count", 10)
        self._min_entries = cfg.get("min_entries_for_thread", 2)

    async def detect(
        self,
        entry_id: str,
        entry_embedding: list[float],
        entry_date: datetime,
    ) -> ThreadMatch:
        """Run thread detection for a newly written entry.

        1. Query ChromaDB for top-N similar entries (excluding self).
        2. Filter to entries above similarity_threshold.
        3. Check thread assignments of similar entries:
           - Similar entries in one thread → join it.
           - Similar entries span threads → join highest avg similarity.
           - 2+ similar unthreaded → create new thread grouping all.
           - <2 similar → unthreaded.
        """
        # Query ChromaDB by embedding vector
        similar = self._query_similar(entry_id, entry_embedding)

        if not similar:
            logger.debug("thread_detect_unthreaded", entry_id=entry_id, reason="no_similar")
            return ThreadMatch(entry_id=entry_id, thread_id=None, match_type="unthreaded")

        similar_ids = [s["id"] for s in similar]
        similar_scores = {s["id"]: s["similarity"] for s in similar}

        # Get thread assignments for similar entries
        thread_assignments: dict[str, list[str]] = {}  # thread_id -> [entry_ids]
        unthreaded_entries: list[str] = []

        for sid in similar_ids:
            threads = await self._store.get_threads_for_entry(sid)
            if threads:
                for t in threads:
                    thread_assignments.setdefault(t.id, []).append(sid)
            else:
                unthreaded_entries.append(sid)

        # Case 1: similar entries belong to existing thread(s)
        if thread_assignments:
            # Pick thread with highest average similarity
            best_thread_id = None
            best_avg = 0.0
            for tid, eids in thread_assignments.items():
                avg_sim = sum(similar_scores.get(e, 0) for e in eids) / len(eids)
                if avg_sim > best_avg:
                    best_avg = avg_sim
                    best_thread_id = tid

            # Join the best thread
            avg_sim_to_thread = best_avg
            await self._store.add_entry(best_thread_id, entry_id, avg_sim_to_thread, entry_date)

            logger.info(
                "thread_detect_joined",
                entry_id=entry_id,
                thread_id=best_thread_id,
                similarity=round(avg_sim_to_thread, 3),
            )
            return ThreadMatch(
                entry_id=entry_id,
                thread_id=best_thread_id,
                match_type="joined_existing",
                similar_entries=similar_ids,
                is_new_thread=False,
            )

        # Case 2: no threaded similar entries — check if enough unthreaded to form new thread
        if len(unthreaded_entries) >= (self._min_entries - 1):
            # Create new thread from the cluster
            # Label = truncated text from the current entry
            label = await self._make_label(entry_id)
            thread = await self._store.create_thread(label)

            # Add all similar unthreaded entries + the new entry
            for uid in unthreaded_entries:
                historical_date = self._get_entry_date(uid, entry_date)
                await self._store.add_entry(
                    thread.id,
                    uid,
                    similar_scores.get(uid, 0),
                    historical_date,
                )
            await self._store.add_entry(thread.id, entry_id, 1.0, entry_date)

            logger.info(
                "thread_detect_created",
                entry_id=entry_id,
                thread_id=thread.id,
                cluster_size=len(unthreaded_entries) + 1,
            )
            return ThreadMatch(
                entry_id=entry_id,
                thread_id=thread.id,
                match_type="created_new",
                similar_entries=similar_ids,
                is_new_thread=True,
            )

        # Case 3: not enough similar entries
        logger.debug(
            "thread_detect_unthreaded",
            entry_id=entry_id,
            reason="insufficient_similar",
            count=len(unthreaded_entries),
        )
        return ThreadMatch(
            entry_id=entry_id,
            thread_id=None,
            match_type="unthreaded",
            similar_entries=similar_ids,
        )

    def _query_similar(self, entry_id: str, entry_embedding: list[float]) -> list[dict]:
        """Query ChromaDB for entries above similarity threshold, excluding self."""
        try:
            collection = self._embeddings.collection
            # Request extra to account for self-match
            n = self._candidate_count + 1
            # Cap at collection count
            total = collection.count()
            if total <= 1:
                return []
            n = min(n, total)

            results = collection.query(
                query_embeddings=[entry_embedding],
                n_results=n,
                include=["distances"],
            )

            similar = []
            if results["ids"] and results["ids"][0]:
                for i, rid in enumerate(results["ids"][0]):
                    if rid == entry_id:
                        continue
                    distance = results["distances"][0][i]
                    similarity = 1.0 - distance  # cosine distance → similarity
                    if similarity >= self._similarity_threshold:
                        similar.append({"id": rid, "similarity": similarity})
                        logger.debug(
                            "thread_candidate",
                            entry_id=entry_id,
                            candidate=rid,
                            similarity=round(similarity, 4),
                        )

            return similar
        except Exception as e:
            logger.warning("thread_query_failed", entry_id=entry_id, error=str(e))
            return []

    async def _make_label(self, entry_id: str) -> str:
        """Generate thread label from entry content — truncated snippet, no LLM."""
        try:
            collection = self._embeddings.collection
            result = collection.get(ids=[entry_id], include=["documents"])
            if result["documents"] and result["documents"][0]:
                text = result["documents"][0]
                # Strip markdown headers, take first meaningful line
                for line in text.split("\n"):
                    line = line.strip().lstrip("#").strip()
                    if len(line) > 10:
                        return line[:80]
                return text[:80]
        except Exception:
            pass
        return "Recurring topic"

    def _get_entry_date(self, entry_id: str, fallback: datetime) -> datetime:
        """Resolve the original created timestamp for an existing entry when available."""
        try:
            collection = self._embeddings.collection
            result = collection.get(ids=[entry_id], include=["metadatas"])
            if result["metadatas"] and result["metadatas"][0]:
                created = result["metadatas"][0].get("created")
                if created:
                    dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
                    return dt.replace(tzinfo=None) if dt.tzinfo else dt
        except Exception:
            pass
        return fallback

    async def reindex_all(self) -> dict:
        """Rebuild all threads from scratch. Process entries chronologically."""
        await self._store.clear_all()

        collection = self._embeddings.collection
        all_data = collection.get(include=["embeddings", "metadatas"])

        if not all_data["ids"]:
            return {"threads_created": 0, "entries_processed": 0, "entries_threaded": 0}

        # Sort by entry date from metadata, fallback to ID
        entries = []
        for i, eid in enumerate(all_data["ids"]):
            meta = all_data["metadatas"][i] if all_data["metadatas"] else {}
            embedding = all_data["embeddings"][i] if all_data["embeddings"] else None
            created = meta.get("created", "")
            try:
                dt = datetime.fromisoformat(str(created).replace("Z", "+00:00")).replace(
                    tzinfo=None
                )
            except (ValueError, TypeError):
                dt = datetime.min
            entries.append({"id": eid, "embedding": embedding, "date": dt})

        entries.sort(key=lambda e: e["date"])

        stats = {"threads_created": 0, "entries_processed": 0, "entries_threaded": 0}
        for entry in entries:
            if entry["embedding"] is None:
                continue
            stats["entries_processed"] += 1
            match = await self.detect(entry["id"], entry["embedding"], entry["date"])
            if match.thread_id:
                stats["entries_threaded"] += 1
                if match.is_new_thread:
                    stats["threads_created"] += 1

        logger.info("thread_reindex_complete", **stats)
        return stats
