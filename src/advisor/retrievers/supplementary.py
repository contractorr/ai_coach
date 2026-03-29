"""Supplementary context retriever (documents, repos, curriculum)."""

from __future__ import annotations

from pathlib import Path

import structlog

logger = structlog.get_logger()


class SupplementaryRetriever:
    """Retrieves context from library documents, GitHub repos, and curriculum."""

    def __init__(
        self,
        user_id: str | None = None,
        intel_db_path: Path | None = None,
        library_index=None,
        max_context_chars: int = 8000,
    ):
        self._user_id = user_id
        self._intel_db_path = intel_db_path
        self._library_index = library_index
        self._max_context_chars = max_context_chars

    def get_document_context(
        self,
        query: str,
        attachment_ids: list[str] | None = None,
        max_items: int = 4,
        max_chars: int = 4000,
    ) -> str:
        """Get indexed Library document context for the current ask."""
        if not self._library_index:
            return ""

        selected: list[dict] = []
        seen_ids: set[str] = set()
        remaining_chars = max_chars

        def add_item(item: dict | None) -> None:
            nonlocal remaining_chars
            if not item:
                return
            report_id = item.get("report_id")
            if not report_id or report_id in seen_ids or len(selected) >= max_items:
                return

            text = (item.get("extracted_text") or item.get("body_text") or "").strip()
            if not text:
                return

            excerpt = text[: min(len(text), max(remaining_chars - 200, 0))].strip()
            if not excerpt:
                return

            selected.append(
                {
                    "report_id": report_id,
                    "title": item.get("title") or "Untitled document",
                    "file_name": item.get("file_name") or "",
                    "source_kind": item.get("source_kind") or "document",
                    "excerpt": excerpt,
                }
            )
            seen_ids.add(report_id)
            remaining_chars -= len(excerpt)

        for attachment_id in attachment_ids or []:
            add_item(self._library_index.get_item_text(attachment_id))
            if remaining_chars <= 0 or len(selected) >= max_items:
                break

        if query and remaining_chars > 0 and len(selected) < max_items:
            for hit in self._library_index.hybrid_search(
                query, limit=max_items * 2, status="ready"
            ):
                add_item(self._library_index.get_item_text(hit["id"]))
                if remaining_chars <= 0 or len(selected) >= max_items:
                    break

        if not selected:
            return ""

        blocks = []
        for item in selected:
            file_label = f" ({item['file_name']})" if item["file_name"] else ""
            blocks.append(f"[DOCUMENT] {item['title']}{file_label}\n{item['excerpt']}")
        return "DOCUMENT CONTEXT:\n" + "\n\n".join(blocks)

    def get_repo_context(self, query: str) -> str:
        """Inject GitHub repo health data when query matches a monitored repo."""
        if not self._user_id or not self._intel_db_path:
            return ""
        try:
            from intelligence.github_repo_store import GitHubRepoStore

            store = GitHubRepoStore(self._intel_db_path)
            repos = store.list_repos(self._user_id)
            if not repos:
                return ""

            query_tokens = set(query.lower().split())
            max_chars = int(self._max_context_chars * 0.05)
            blocks = []
            chars_used = 0

            for repo in repos:
                repo_name = repo.repo_full_name.split("/")[-1].lower()
                goal_tokens = set()
                if repo.linked_goal_path:
                    goal_title = (
                        repo.linked_goal_path.rsplit("/", 1)[-1]
                        .replace(".md", "")
                        .replace("-", " ")
                    )
                    goal_tokens = set(goal_title.lower().split())

                match_tokens = {repo_name} | goal_tokens
                if not (query_tokens & match_tokens):
                    continue

                snapshot = store.get_latest_snapshot(repo.id)
                if not snapshot:
                    continue

                trend = "unknown"
                wc = snapshot.weekly_commits
                if len(wc) >= 8:
                    recent = sum(wc[-4:]) / 4.0
                    prior = sum(wc[-8:-4]) / 4.0
                    if recent > prior * 1.2:
                        trend = "increasing"
                    elif recent < prior * 0.8:
                        trend = "declining"
                    else:
                        trend = "steady"

                goal_attr = ""
                if repo.linked_goal_path:
                    goal_title = (
                        repo.linked_goal_path.rsplit("/", 1)[-1]
                        .replace(".md", "")
                        .replace("-", " ")
                    )
                    goal_attr = f' linked_goal="{goal_title}"'

                pushed = (
                    snapshot.pushed_at.strftime("%Y-%m-%d") if snapshot.pushed_at else "unknown"
                )
                block = (
                    f'<github_project repo="{repo.repo_full_name}"{goal_attr}>\n'
                    f"  Last commit: {pushed}\n"
                    f"  Commits (30d): {snapshot.commits_30d} ({trend})\n"
                    f"  Open issues: {snapshot.open_issues} | Open PRs: {snapshot.open_prs}\n"
                    f"  CI: {snapshot.ci_status}\n"
                    f"  Latest release: {snapshot.latest_release or 'none'}\n"
                    f"</github_project>"
                )
                if chars_used + len(block) > max_chars:
                    break
                blocks.append(block)
                chars_used += len(block)

            return "\n".join(blocks)
        except Exception as e:
            logger.debug("repo_context_skipped", error=str(e))
            return ""

    def get_curriculum_context(self, query: str = "", max_chars: int = 1500) -> str:
        """Get curriculum progress context for advisor prompt injection."""
        if not self._user_id or not self._intel_db_path:
            return ""
        try:
            from curriculum.personalization import build_learning_signal_map
            from curriculum.store import CurriculumStore
            from journal.storage import JournalStorage
            from web.deps import get_user_paths

            paths = get_user_paths(self._user_id)
            db_path = Path(paths["data_dir"]) / "curriculum.db"
            if not db_path.exists():
                return ""
            store = CurriculumStore(db_path)
            enrollments = store.get_enrollments(self._user_id)
            active = [e for e in enrollments if not e.get("completed_at")][:5]
            if not active:
                return ""

            storage = JournalStorage(paths["journal_dir"])
            assessment_artifacts: list[dict] = []
            for entry in storage.list_entries(limit=100):
                try:
                    post = storage.read(entry["path"])
                except Exception:
                    continue
                metadata = dict(post.metadata)
                guide_id = metadata.get("curriculum_guide_id")
                assessment_type = metadata.get("curriculum_assessment_type")
                status_value = metadata.get("assessment_status")
                if (
                    not guide_id
                    or not assessment_type
                    or status_value
                    not in {
                        "draft",
                        "active",
                        "submitted",
                    }
                ):
                    continue
                assessment_artifacts.append(
                    {
                        "guide_id": guide_id,
                        "assessment_type": assessment_type,
                        "draft_status": status_value,
                        "draft_feedback": metadata.get("assessment_feedback"),
                    }
                )

            learning_signal_map = build_learning_signal_map(
                store.list_review_items(self._user_id, include_pre_reading=False),
                assessment_artifacts,
            )
            due_reviews = len(store.get_due_reviews(self._user_id, limit=20))
            retry_reviews = len(store.get_retry_review_items(self._user_id, limit=20))

            weak_reviews = 0
            active_revisions = 0
            submitted_assessments = 0
            for enrollment in active:
                learning_signals = learning_signal_map.get(enrollment["guide_id"], {})
                weak_reviews += int(learning_signals.get("weak_review_count") or 0)
                active_revisions += int(learning_signals.get("revision_backlog_count") or 0)
                submitted_assessments += int(
                    learning_signals.get("submitted_assessment_count") or 0
                )

            lines = ["<curriculum_progress>"]
            lines.append(
                "  <learning_pressure "
                f'due_reviews="{due_reviews}" '
                f'retry_reviews="{retry_reviews}" '
                f'weak_reviews="{weak_reviews}" '
                f'active_revisions="{active_revisions}" '
                f'submitted_assessments="{submitted_assessments}" />'
            )
            for enrollment in active:
                guide = store.get_guide(enrollment["guide_id"])
                if not guide:
                    continue
                chapters = guide.get("chapters", [])
                total = len(chapters)
                completed = 0
                if chapters:
                    for ch in chapters:
                        prog = store.get_chapter_progress(self._user_id, ch["id"])
                        if prog and prog.get("status") == "completed":
                            completed += 1
                track_attr = f' track="{guide.get("track", "")}"' if guide.get("track") else ""
                learning_signals = learning_signal_map.get(enrollment["guide_id"], {})
                weak_attr = ""
                if learning_signals.get("weak_review_count"):
                    weak_attr = f' weak_reviews="{learning_signals["weak_review_count"]}"'
                revision_attr = ""
                if learning_signals.get("revision_backlog_count"):
                    revision_attr = (
                        f' revision_backlog="{learning_signals["revision_backlog_count"]}"'
                    )
                grade_attr = ""
                if learning_signals.get("average_assessment_grade") is not None:
                    grade_attr = (
                        f' avg_assessment_grade="{learning_signals["average_assessment_grade"]}"'
                    )
                submitted_attr = ""
                if learning_signals.get("submitted_assessment_count"):
                    submitted_attr = (
                        f' submitted_assessments="{learning_signals["submitted_assessment_count"]}"'
                    )
                lines.append(
                    f'  <guide id="{guide["id"]}" title="{guide["title"]}" '
                    f'progress="{completed}/{total}"{track_attr}{weak_attr}'
                    f"{revision_attr}{grade_attr}{submitted_attr} />"
                )
            lines.append("</curriculum_progress>")
            result = "\n".join(lines)
            return result if len(result) <= max_chars else result[:max_chars]
        except Exception as e:
            logger.debug("curriculum_context_skipped", error=str(e))
            return ""
