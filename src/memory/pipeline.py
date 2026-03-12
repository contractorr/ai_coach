"""Memory pipeline orchestrates extract -> resolve -> store."""

import structlog

from .extractor import FactExtractor
from .models import FactSource, FactUpdate
from .resolver import ConflictResolver
from .store import FactStore

logger = structlog.get_logger()


class MemoryPipeline:
    """Orchestrates the full extract -> resolve -> store pipeline."""

    def __init__(
        self,
        store: FactStore,
        extractor: FactExtractor | None = None,
        resolver: ConflictResolver | None = None,
        consolidator=None,
    ):
        self.store = store
        self.extractor = extractor or FactExtractor()
        self.resolver = resolver or ConflictResolver(store)
        self.consolidator = consolidator

    def process_journal_entry(
        self, entry_id: str, entry_text: str, entry_metadata: dict | None = None
    ) -> list[FactUpdate]:
        """Full pipeline for a journal entry."""
        candidates = self.extractor.extract_from_journal(entry_id, entry_text, entry_metadata)
        if not candidates:
            return []

        updates = self.resolver.resolve(candidates)
        self._execute(updates, candidates)
        self._maybe_consolidate(updates, candidates)

        logger.info(
            "memory.journal_processed",
            entry_id=entry_id,
            extracted=len(candidates),
            actions={u.action for u in updates},
        )
        return updates

    def process_feedback(
        self, recommendation_id: str, feedback: str, context: dict | None = None
    ) -> list[FactUpdate]:
        """Pipeline for recommendation feedback."""
        candidates = self.extractor.extract_from_feedback(recommendation_id, feedback, context)
        if not candidates:
            return []

        updates = self.resolver.resolve(candidates)
        self._execute(updates, candidates)
        self._maybe_consolidate(updates, candidates)

        logger.info(
            "memory.feedback_processed",
            recommendation_id=recommendation_id,
            extracted=len(candidates),
        )
        return updates

    def process_goal_event(
        self, goal_id: str, event_type: str, goal_data: dict
    ) -> list[FactUpdate]:
        """Pipeline for goal creation, milestone completion, etc."""
        goal_data = {**goal_data, "event_type": event_type}
        candidates = self.extractor.extract_from_goal(goal_id, goal_data)
        if not candidates:
            return []

        updates = self.resolver.resolve(candidates)
        self._execute(updates, candidates)
        self._maybe_consolidate(updates, candidates)

        logger.info(
            "memory.goal_processed",
            goal_id=goal_id,
            event_type=event_type,
            extracted=len(candidates),
        )
        return updates

    def process_document(
        self, document_id: str, document_text: str, document_metadata: dict | None = None
    ) -> list[FactUpdate]:
        """Pipeline for an uploaded document such as a CV."""
        candidates = self.extractor.extract_from_document(
            document_id,
            document_text,
            document_metadata,
        )
        if not candidates:
            return []

        updates = self.resolver.resolve(candidates)
        self._execute(updates, candidates)
        self._maybe_consolidate(updates, candidates)

        logger.info(
            "memory.document_processed",
            document_id=document_id,
            extracted=len(candidates),
            actions={u.action for u in updates},
        )
        return updates

    def backfill(self, journal_entries: list[dict]) -> dict:
        """Process all existing journal entries in chronological order."""
        stats = {
            "entries_processed": 0,
            "facts_extracted": 0,
            "facts_stored": 0,
        }

        sorted_entries = sorted(journal_entries, key=lambda e: e.get("created", "") or "")

        for entry in sorted_entries:
            entry_id = entry.get("path", entry.get("id", ""))
            content = entry.get("content", "")
            metadata = {
                "type": entry.get("type", ""),
                "tags": entry.get("tags", []),
            }

            if not content or len(content.strip()) < 20:
                continue

            candidates = self.extractor.extract_from_journal(entry_id, content, metadata)
            stats["facts_extracted"] += len(candidates)

            if candidates:
                updates = self.resolver.resolve(candidates)
                stored = self._execute(updates, candidates)
                stats["facts_stored"] += stored

            stats["entries_processed"] += 1

        if self.consolidator:
            try:
                observations = self.consolidator.consolidate_all()
                stats["observations_created"] = len(observations)
            except Exception as e:
                logger.warning("backfill_consolidation_failed", error=str(e))

        logger.info("memory.backfill_complete", **stats)
        return stats

    def reextract_entry(
        self, entry_id: str, entry_text: str, entry_metadata: dict | None = None
    ) -> list[FactUpdate]:
        """Re-extract facts from a single entry. Deletes old facts first."""
        self.store.delete_by_source(FactSource.JOURNAL, entry_id)
        return self.process_journal_entry(entry_id, entry_text, entry_metadata)

    def reextract_document(
        self, document_id: str, document_text: str, document_metadata: dict | None = None
    ) -> list[FactUpdate]:
        """Re-extract facts from a single uploaded document."""
        self.store.delete_by_source(FactSource.DOCUMENT, document_id)
        return self.process_document(document_id, document_text, document_metadata)

    def _maybe_consolidate(self, updates: list[FactUpdate], candidates: list) -> None:
        """Trigger incremental observation consolidation for newly stored facts."""
        if not self.consolidator:
            return
        stored_ids = [
            c.id
            for u, c in zip(updates, candidates, strict=False)
            if u.action in ("ADD", "UPDATE") and c and c.id
        ]
        if stored_ids:
            try:
                self.consolidator.consolidate_affected(stored_ids)
            except Exception as e:
                logger.warning("consolidation_failed", error=str(e))

    def _execute(self, updates: list[FactUpdate], candidates: list) -> int:
        """Execute resolved actions. Returns count of facts stored."""
        stored = 0

        for update, candidate in zip(updates, candidates, strict=False):
            if update.action == "ADD":
                if candidate:
                    self.store.add(candidate)
                    stored += 1

            elif update.action == "UPDATE" and update.existing_id:
                if candidate:
                    self.store.update(
                        update.existing_id,
                        candidate.text,
                        candidate.source_id,
                        new_source_type=candidate.source_type,
                        new_category=candidate.category,
                        new_confidence=candidate.confidence,
                    )
                    stored += 1

            elif update.action == "DELETE" and update.existing_id:
                self.store.delete(update.existing_id, reason=update.reasoning)

            elif update.action == "NOOP" and update.existing_id:
                self.store.reinforce(update.existing_id)

        return stored
