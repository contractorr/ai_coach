"""Curriculum / Learn routes — guides, chapters, progress, reviews, quizzes, placement."""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from curriculum.content_schema import (
    derive_causal_lens,
    derive_guide_synthesis,
    derive_misconception_card,
    load_curriculum_document,
    resolve_chapter_content_path,
)
from curriculum.guide_generator import GuideGenerationService
from curriculum.models import (
    BloomLevel,
    ChapterStatus,
    GuideExtensionRequest,
    GuideGenerationRequest,
    ProgressUpdate,
    QuizSubmission,
    ReviewGradeRequest,
    ReviewItemType,
)
from curriculum.personalization import (
    build_applied_assessments,
    build_learning_signal_map,
    empty_learning_signal_summary,
    score_guide_candidate,
)
from curriculum.question_generator import QuestionGenerator
from curriculum.scanner import CurriculumScanner, build_tree_layout
from curriculum.store import CurriculumStore
from curriculum.user_content import ensure_user_curriculum_dirs, load_guide_metadata
from llm import LLMError, create_cheap_provider, create_llm_provider
from web.auth import get_current_user
from web.deps import (
    SHARED_LLM_MODEL,
    get_config,
    get_profile_path,
    get_user_paths,
    resolve_llm_credentials_for_user,
)
from web.models import (
    CurriculumChapterDetailResponse,
    CurriculumGuideDetailResponse,
    CurriculumReviewItemResponse,
)
from web.user_store import log_event

logger = structlog.get_logger()
router = APIRouter(prefix="/api/curriculum", tags=["curriculum"])


def _content_dirs(user_id: str | None = None) -> list[Path]:
    """Resolve built-in + extra content directories."""
    # Built-in content: content/curriculum/ relative to repo root
    # Repo root = 3 levels up from src/web/routes/
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    dirs = [repo_root / "content" / "curriculum"]

    config = get_config()
    if hasattr(config, "curriculum") and config.curriculum.extra_content_dirs:
        for d in config.curriculum.extra_content_dirs:
            dirs.append(Path(d).expanduser().resolve())
    if user_id:
        active_dir, _ = ensure_user_curriculum_dirs(user_id)
        dirs.append(active_dir)
    return dirs


def _get_store(user_id: str) -> CurriculumStore:
    paths = get_user_paths(user_id)
    return CurriculumStore(Path(paths["data_dir"]) / "curriculum.db")


def _get_scanner(user_id: str, store: CurriculumStore | None = None) -> CurriculumScanner:
    store = store or _get_store(user_id)
    return _ensure_catalog_initialized(store, CurriculumScanner(_content_dirs(user_id)))


def _build_question_generator(user_id: str) -> QuestionGenerator:
    provider_name, api_key, source = resolve_llm_credentials_for_user(user_id)
    if not api_key:
        return QuestionGenerator()

    config = get_config()
    provider = provider_name or config.llm.provider
    model = SHARED_LLM_MODEL if source == "shared" else config.llm.model

    try:
        llm = create_llm_provider(provider=provider, api_key=api_key, model=model)
        cheap_llm = create_cheap_provider(provider=provider, api_key=api_key)
        return QuestionGenerator(llm_provider=llm, cheap_llm_provider=cheap_llm)
    except LLMError as exc:
        logger.warning("curriculum.llm_init_failed", user_id=user_id, error=str(exc))
        return QuestionGenerator()


def _build_guide_generation_service(user_id: str) -> GuideGenerationService:
    provider_name, api_key, source = resolve_llm_credentials_for_user(user_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail="Guide generation requires configured LLM credentials.",
        )

    config = get_config()
    provider = provider_name or config.llm.provider
    model = SHARED_LLM_MODEL if source == "shared" else config.llm.model

    try:
        llm = create_llm_provider(provider=provider, api_key=api_key, model=model)
    except LLMError as exc:
        logger.warning(
            "curriculum.guide_generation.llm_init_failed", user_id=user_id, error=str(exc)
        )
        raise HTTPException(status_code=503, detail="Guide generation is currently unavailable.")

    active_dir, _ = ensure_user_curriculum_dirs(user_id)
    return GuideGenerationService(
        llm_provider=llm,
        output_root=active_dir,
        owner_user_id=user_id,
        max_chapters=config.curriculum.user_guide_max_chapters,
    )


def _ensure_catalog_initialized(
    store: CurriculumStore,
    scanner: CurriculumScanner | None = None,
    user_id: str | None = None,
) -> CurriculumScanner:
    """Populate the curriculum catalog on first use for this user DB."""
    scanner = scanner or CurriculumScanner(_content_dirs(user_id))
    current_fingerprint = scanner.get_catalog_fingerprint()
    stored_fingerprint = store.get_catalog_meta("catalog_fingerprint")
    if not store.list_guides() or stored_fingerprint != current_fingerprint:
        _sync_catalog(
            store,
            user_id=user_id,
            scanner=scanner,
            catalog_fingerprint=current_fingerprint,
        )
    return scanner


def _build_program_lookup(programs: list[dict]) -> dict[str, list[dict]]:
    """Map guide_id -> curated learning programs containing that guide."""
    lookup: dict[str, list[dict]] = {}
    for program in programs:
        summary = {
            "id": program["id"],
            "title": program["title"],
            "audience": program.get("audience", ""),
            "description": program.get("description", ""),
            "color": program.get("color", "#6b7280"),
            "outcomes": list(program.get("outcomes", [])),
            "guide_ids": list(program.get("guide_ids", [])),
            "applied_module_ids": list(program.get("applied_module_ids", [])),
        }
        for guide_id in [*summary["guide_ids"], *summary["applied_module_ids"]]:
            lookup.setdefault(guide_id, []).append(summary)
    return lookup


def _load_user_profile(user_id: str):
    try:
        from profile.storage import ProfileStorage

        return ProfileStorage(get_profile_path(user_id)).load()
    except Exception as exc:
        logger.warning("curriculum.profile_load_failed", user_id=user_id, error=str(exc))
        return None


_ASSESSMENT_STAGE_LABELS = {
    "chapter_completion": "After chapter",
    "review": "Review",
    "scenario_practice": "Scenario",
    "capstone": "Capstone",
}


def _assessment_draft_key(guide_id: str, assessment_type: str) -> str:
    return f"{guide_id}:{assessment_type}"


def _assessment_entry_type(assessment_type: str) -> str:
    return {
        "teach_back": "reflection",
        "decision_brief": "action_brief",
        "scenario_analysis": "note",
        "case_memo": "action_brief",
    }.get(assessment_type, "note")


def _list_assessment_drafts(
    user_id: str,
    *,
    guide_id: str | None = None,
    allowed_statuses: set[str] | None = None,
) -> dict[str, dict]:
    from journal.storage import JournalStorage

    storage = JournalStorage(get_user_paths(user_id)["journal_dir"])
    drafts: dict[str, dict] = {}
    allowed_statuses = allowed_statuses or {"draft", "active", "submitted"}

    for entry_path in sorted(storage.journal_dir.glob("*.md"), reverse=True):
        try:
            post = storage.read(entry_path)
        except Exception:
            continue

        metadata = dict(post.metadata)
        entry_guide_id = metadata.get("curriculum_guide_id")
        assessment_type = metadata.get("curriculum_assessment_type")
        draft_status = metadata.get("assessment_status", "draft")
        if not entry_guide_id or not assessment_type or draft_status not in allowed_statuses:
            continue
        if guide_id and entry_guide_id != guide_id:
            continue

        key = _assessment_draft_key(entry_guide_id, assessment_type)
        sort_key = metadata.get("updated") or metadata.get("created") or ""
        existing = drafts.get(key)
        if existing and existing["sort_key"] >= sort_key:
            continue

        drafts[key] = {
            "guide_id": entry_guide_id,
            "assessment_type": assessment_type,
            "entry_path": str(entry_path),
            "entry_title": metadata.get("title", entry_path.stem),
            "goal_path": metadata.get("linked_goal_path"),
            "goal_title": metadata.get("linked_goal_title"),
            "draft_status": draft_status,
            "draft_feedback": metadata.get("assessment_feedback"),
            "sort_key": sort_key,
        }

    return drafts


def _attach_assessment_drafts(
    guide_id: str,
    assessments: list[dict],
    draft_map: dict[str, dict],
) -> list[dict]:
    enriched: list[dict] = []
    for assessment in assessments:
        draft = draft_map.get(_assessment_draft_key(guide_id, assessment["type"]))
        if not draft:
            enriched.append(assessment)
            continue
        enriched.append(
            {
                **assessment,
                "draft_entry_path": draft["entry_path"],
                "draft_entry_title": draft["entry_title"],
                "draft_goal_path": draft.get("goal_path"),
                "draft_goal_title": draft.get("goal_title"),
                "draft_status": draft.get("draft_status"),
                "draft_feedback": draft.get("draft_feedback"),
            }
        )
    return enriched


def _build_assessment_entry_content(guide: dict, assessment: dict) -> str:
    focus_lines = "\n".join(f"- {item}" for item in assessment["evaluation_focus"])
    stage_label = _ASSESSMENT_STAGE_LABELS.get(assessment["stage"], assessment["stage"])
    return f"""# {assessment["title"]}

Guide: {guide["title"]}
Stage: {stage_label}
Deliverable: {assessment["deliverable"]}

## Prompt
{assessment["prompt"]}

## Evaluation Focus
{focus_lines}

## Draft

### Recommendation

### Reasoning

### Risks and Failure Modes

### Signals to Watch
"""


def _build_assessment_goal_content(guide: dict, assessment: dict) -> str:
    focus_lines = "\n".join(f"- {item}" for item in assessment["evaluation_focus"])
    return f"""Complete the applied assessment **{assessment["title"]}** for **{guide["title"]}**.

Deliverable: {assessment["deliverable"]}

Prompt:
{assessment["prompt"]}

Evaluate the work against:
{focus_lines}
"""


def _schedule_curriculum_entry_hooks(user_id: str, entry_path: Path, storage) -> None:
    post = storage.read(entry_path)
    try:
        from journal.extraction_receipts import ReceiptBuilder
        from web.deps import get_receipt_store

        ReceiptBuilder(get_receipt_store(user_id)).seed_pending(
            str(entry_path),
            post.get("title", entry_path.stem),
        )
    except Exception as exc:
        logger.warning(
            "curriculum.assessment_receipt_seed_failed",
            user_id=user_id,
            entry_path=str(entry_path),
            error=str(exc),
        )

    try:
        from web.routes.journal import _schedule_post_create_hooks

        _schedule_post_create_hooks(user_id, entry_path, post.content, dict(post.metadata))
    except Exception as exc:
        logger.warning(
            "curriculum.assessment_post_create_failed",
            user_id=user_id,
            entry_path=str(entry_path),
            error=str(exc),
        )


def _format_assessment_feedback(result: dict) -> dict:
    return {
        "grade": result["grade"],
        "feedback": result["feedback"],
        "correct_points": result["correct_points"],
        "missing_points": result["missing_points"],
        "graded_at": datetime.utcnow().isoformat(),
    }


def _complete_goal_milestone_if_present(goal_path: str | None, index: int, user_id: str) -> None:
    if not goal_path:
        return
    try:
        from advisor.goals import GoalTracker
        from journal.storage import JournalStorage

        storage = JournalStorage(get_user_paths(user_id)["journal_dir"])
        GoalTracker(storage).complete_milestone(Path(goal_path), index)
    except Exception as exc:
        logger.warning(
            "curriculum.assessment_goal_milestone_failed",
            user_id=user_id,
            goal_path=goal_path,
            milestone_index=index,
            error=str(exc),
        )


def _update_goal_status_if_present(goal_path: str | None, status_value: str, user_id: str) -> None:
    if not goal_path:
        return
    try:
        from advisor.goals import GoalTracker
        from journal.storage import JournalStorage

        storage = JournalStorage(get_user_paths(user_id)["journal_dir"])
        GoalTracker(storage).update_goal_status(Path(goal_path), status_value)
    except Exception as exc:
        logger.warning(
            "curriculum.assessment_goal_status_failed",
            user_id=user_id,
            goal_path=goal_path,
            status=status_value,
            error=str(exc),
        )


def _get_applied_assessment_definition(
    *,
    user_id: str,
    store: CurriculumStore,
    scanner: CurriculumScanner,
    guide_id: str,
    assessment_type: str,
) -> tuple[dict, dict]:
    program_lookup = _build_program_lookup(scanner.get_learning_programs())
    profile = _load_user_profile(user_id)
    guide = store.get_guide(guide_id, user_id=user_id)
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    next_chapter = store.get_next_chapter(user_id, guide_id)
    decorated_guide = _decorate_guide_payload(
        guide,
        scanner,
        program_lookup,
        profile=profile,
        include_applied_assessments=True,
        assessment_chapter_title=next_chapter["title"] if next_chapter else None,
    )
    assessments = decorated_guide.get("applied_assessments", [])
    assessment = next((item for item in assessments if item["type"] == assessment_type), None)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return guide, assessment


def _get_applied_assessment_artifact(
    user_id: str,
    *,
    guide_id: str,
    assessment_type: str,
) -> dict | None:
    return _list_assessment_drafts(
        user_id,
        guide_id=guide_id,
        allowed_statuses={"draft", "active", "submitted"},
    ).get(_assessment_draft_key(guide_id, assessment_type))


def _build_learning_signal_map(user_id: str, store: CurriculumStore) -> dict[str, dict]:
    return build_learning_signal_map(
        store.list_review_items(user_id, include_pre_reading=False),
        list(
            _list_assessment_drafts(
                user_id,
                allowed_statuses={"draft", "active", "submitted"},
            ).values()
        ),
    )


def _guide_learning_signals(learning_signal_map: dict[str, dict], guide_id: str) -> dict:
    return learning_signal_map.get(guide_id, empty_learning_signal_summary())


def _decorate_guide_payload(
    guide: dict,
    scanner: CurriculumScanner,
    program_lookup: dict[str, list[dict]] | None = None,
    *,
    store: CurriculumStore | None = None,
    user_id: str | None = None,
    profile=None,
    include_applied_assessments: bool = False,
    assessment_chapter_title: str | None = None,
) -> dict:
    """Attach manifest-driven program metadata to a guide payload."""
    canonical_guide_id = scanner.canonicalize_guide_id(guide["id"])
    if program_lookup is None:
        program_lookup = _build_program_lookup(scanner.get_learning_programs())
    programs = program_lookup.get(canonical_guide_id, [])
    payload = {
        **guide,
        "canonical_guide_id": canonical_guide_id if canonical_guide_id != guide["id"] else None,
        "learning_programs": programs,
        "linked_extensions": [],
    }
    if store is not None:
        payload["linked_extensions"] = [
            _decorate_guide_payload(extension, scanner, program_lookup)
            for extension in store.list_linked_extensions(
                guide["id"],
                user_id=user_id,
            )
        ]
    if include_applied_assessments:
        payload["applied_assessments"] = build_applied_assessments(
            payload,
            programs,
            profile,
            chapter_title=assessment_chapter_title,
        )
    return payload


def _resolve_guide_id(scanner: CurriculumScanner, guide_id: str) -> str:
    """Resolve manifest aliases to the canonical guide ID."""
    return scanner.canonicalize_guide_id(guide_id)


def _resolve_chapter_id(scanner: CurriculumScanner, chapter_id: str) -> str:
    """Resolve manifest aliases embedded in a full chapter ID."""
    if "/" not in chapter_id:
        return chapter_id
    raw_guide_id, chapter_stem = chapter_id.split("/", 1)
    return f"{_resolve_guide_id(scanner, raw_guide_id)}/{chapter_stem}"


def _ensure_user_guide_mutable(guide: dict) -> None:
    if guide.get("origin") != "user":
        raise HTTPException(status_code=403, detail="Built-in guides cannot be modified.")
    if guide.get("archived_at"):
        raise HTTPException(status_code=409, detail="Guide is archived.")


def _load_current_cached_artifacts(
    store: CurriculumStore,
    *,
    user_id: str,
    chapter_id: str,
    content_hash: str,
    item_types: set[str],
) -> list[dict]:
    """Return current cached chapter artifacts, evicting stale ones first."""
    items = [
        item
        for item in store.get_review_items_for_chapter(user_id, chapter_id)
        if item.get("item_type") in item_types
    ]
    if not items:
        return []
    if any(item.get("content_hash") != content_hash for item in items):
        store.delete_review_items_for_chapter(user_id, chapter_id, sorted(item_types))
        return []
    return items


def _recommendation_reason(stage: str, recommendation_meta: dict, fallback: str) -> str:
    matched_programs = recommendation_meta.get("matched_programs", [])
    if matched_programs and stage in {"ready", "entry"}:
        return f"Best fit right now for {matched_programs[0]['title']}."
    signals = recommendation_meta.get("signals", [])
    if stage in {"continue", "enrolled"}:
        for signal in signals:
            if signal.get("kind") in {"assessment", "performance"}:
                return signal.get("detail", fallback)
    if stage in {"ready", "entry"}:
        for signal in signals:
            if signal.get("kind") in {"context", "industry", "time", "assessment"}:
                return signal.get("detail", fallback)
    return fallback


def _build_next_payload(
    guide: dict,
    scanner: CurriculumScanner,
    program_lookup: dict[str, list[dict]],
    profile,
    learning_signal_map: dict[str, dict],
    *,
    stage: str,
    chapter: dict | None,
    action: str | None,
    fallback_reason: str,
) -> dict:
    decorated_guide = _decorate_guide_payload(guide, scanner, program_lookup)
    recommendation_meta = score_guide_candidate(
        decorated_guide,
        decorated_guide["learning_programs"],
        profile,
        stage=stage,
        learning_signals=_guide_learning_signals(learning_signal_map, decorated_guide["id"]),
    )
    return {
        "guide_id": decorated_guide["id"],
        "guide_title": decorated_guide["title"],
        "chapter": chapter,
        "reason": _recommendation_reason(stage, recommendation_meta, fallback_reason),
        "action": action,
        "recommendation_type": stage,
        "signals": recommendation_meta["signals"],
        "matched_programs": recommendation_meta["matched_programs"],
        "applied_assessments": build_applied_assessments(
            decorated_guide,
            decorated_guide["learning_programs"],
            profile,
            chapter_title=chapter["title"] if chapter else None,
        ),
    }


def _pick_best_candidate(candidates: list[dict]) -> dict | None:
    if not candidates:
        return None
    ranked = sorted(candidates, key=lambda item: (-item["meta"]["score"], item["guide"]["title"]))
    return ranked[0]


def _get_next_recommendation_v2(
    user_id: str,
    store: CurriculumStore,
    scanner: CurriculumScanner,
    guide_aliases: set[str],
):

    program_lookup = _build_program_lookup(scanner.get_learning_programs())
    profile = _load_user_profile(user_id)
    learning_signal_map = _build_learning_signal_map(user_id, store)

    last = store.get_last_read_chapter(user_id)
    if last:
        next_ch = store.get_next_chapter(user_id, last["guide_id"])
        if next_ch:
            guide = store.get_guide(last["guide_id"], user_id=user_id) or store.get_guide(
                last["guide_id"]
            )
            if guide:
                return _build_next_payload(
                    guide,
                    scanner,
                    program_lookup,
                    profile,
                    learning_signal_map,
                    stage="continue",
                    chapter=next_ch,
                    action=None,
                    fallback_reason="Continue where you left off.",
                )

    enrolled_candidates = []
    for enrollment in store.get_enrollments(user_id):
        if enrollment.get("completed_at"):
            continue
        guide = store.get_guide(enrollment["guide_id"], user_id=user_id) or store.get_guide(
            enrollment["guide_id"]
        )
        if not guide:
            continue
        next_ch = store.get_next_chapter(user_id, enrollment["guide_id"])
        if not next_ch:
            continue
        decorated = _decorate_guide_payload(guide, scanner, program_lookup)
        enrolled_candidates.append(
            {
                "guide": guide,
                "chapter": next_ch,
                "meta": score_guide_candidate(
                    decorated,
                    decorated["learning_programs"],
                    profile,
                    stage="enrolled",
                    learning_signals=_guide_learning_signals(learning_signal_map, guide["id"]),
                ),
            }
        )
    best_enrolled = _pick_best_candidate(enrolled_candidates)
    if best_enrolled:
        return _build_next_payload(
            best_enrolled["guide"],
            scanner,
            program_lookup,
            profile,
            learning_signal_map,
            stage="enrolled",
            chapter=best_enrolled["chapter"],
            action=None,
            fallback_reason="Continue your current enrolled guide.",
        )

    ready_candidates = []
    for ready_guide in store.get_ready_guides(user_id, excluded_guide_ids=guide_aliases):
        guide = store.get_guide(ready_guide["id"], user_id=user_id) or store.get_guide(
            ready_guide["id"]
        )
        if not guide:
            continue
        decorated = _decorate_guide_payload(guide, scanner, program_lookup)
        ready_candidates.append(
            {
                "guide": guide,
                "meta": score_guide_candidate(
                    decorated,
                    decorated["learning_programs"],
                    profile,
                    stage="ready",
                    learning_signals=_guide_learning_signals(learning_signal_map, guide["id"]),
                ),
            }
        )
    best_ready = _pick_best_candidate(ready_candidates)
    if best_ready:
        return _build_next_payload(
            best_ready["guide"],
            scanner,
            program_lookup,
            profile,
            learning_signal_map,
            stage="ready",
            chapter=None,
            action="enroll",
            fallback_reason="Prerequisites are complete and this is the strongest next unlocked guide.",
        )

    entry_candidates = []
    all_guides = [
        guide for guide in store.list_guides(user_id=user_id) if guide["id"] not in guide_aliases
    ]
    for guide in all_guides:
        prereqs = guide.get("prerequisites", [])
        if isinstance(prereqs, str):
            prereqs = json.loads(prereqs)
        if prereqs or store.is_enrolled(user_id, guide["id"]):
            continue
        decorated = _decorate_guide_payload(guide, scanner, program_lookup)
        entry_candidates.append(
            {
                "guide": guide,
                "meta": score_guide_candidate(
                    decorated,
                    decorated["learning_programs"],
                    profile,
                    stage="entry",
                    learning_signals=_guide_learning_signals(learning_signal_map, guide["id"]),
                ),
            }
        )
    best_entry = _pick_best_candidate(entry_candidates)
    if best_entry:
        return _build_next_payload(
            best_entry["guide"],
            scanner,
            program_lookup,
            profile,
            learning_signal_map,
            stage="entry",
            chapter=None,
            action="enroll",
            fallback_reason="Suggested entry point with no prerequisites.",
        )

    return {
        "guide_id": None,
        "chapter": None,
        "reason": "No active guides - enroll in one to get started.",
        "recommendation_type": "fallback",
        "signals": [],
        "matched_programs": [],
        "applied_assessments": [],
    }


def _recommendation_priority(stage: str | None) -> int:
    return {
        "continue": 110,
        "enrolled": 102,
        "ready": 78,
        "entry": 64,
        "fallback": 12,
    }.get(stage or "fallback", 12)


def _estimate_task_minutes(
    *,
    chapter: dict | None = None,
    guide: dict | None = None,
    review_count: int = 0,
    assessment: dict | None = None,
) -> int:
    if review_count > 0:
        return max(5, min(review_count * 4, 25))
    if assessment is not None:
        return 20 if assessment.get("stage") == "review" else 25
    if chapter and chapter.get("reading_time_minutes"):
        return max(5, int(chapter["reading_time_minutes"]))
    if guide and guide.get("total_reading_time_minutes"):
        return max(10, min(int(guide["total_reading_time_minutes"]), 30))
    return 10


def _build_today_task_from_recommendation(
    recommendation: dict,
    store: CurriculumStore,
    user_id: str,
) -> dict | None:
    guide_id = recommendation.get("guide_id")
    if not guide_id:
        return None

    chapter = recommendation.get("chapter")
    guide = store.get_guide(guide_id, user_id=user_id) or store.get_guide(guide_id)
    stage = recommendation.get("recommendation_type")

    if chapter:
        title = f"Resume {chapter['title']}"
        detail = recommendation.get("reason") or "Pick up the next chapter in your active guide."
        cta_label = "Resume lesson"
        task_type = "continue_chapter"
    else:
        guide_title = recommendation.get("guide_title") or (guide or {}).get("title") or guide_id
        title = f"Start {guide_title}"
        detail = (
            recommendation.get("reason") or "Open the strongest next guide for your current path."
        )
        cta_label = "Open guide"
        task_type = "start_guide"

    return {
        "id": f"recommendation:{guide_id}:{chapter['id'] if chapter else stage}",
        "task_type": task_type,
        "title": title,
        "detail": detail,
        "cta_label": cta_label,
        "priority": _recommendation_priority(stage),
        "estimate_minutes": _estimate_task_minutes(chapter=chapter, guide=guide),
        "guide_id": guide_id,
        "guide_title": recommendation.get("guide_title") or (guide or {}).get("title"),
        "chapter_id": chapter["id"] if chapter else None,
        "chapter_title": chapter["title"] if chapter else None,
        "recommendation_type": stage,
        "signals": recommendation.get("signals", []),
        "matched_programs": recommendation.get("matched_programs", []),
        "assessment": None,
    }


def _build_review_task(
    store: CurriculumStore,
    user_id: str,
    review_count: int,
) -> dict | None:
    if review_count <= 0:
        return None

    queue_preview = store.get_review_queue(user_id, limit=min(review_count, 3))
    guide_titles: list[str] = []
    for item in queue_preview:
        guide = store.get_guide(item["guide_id"])
        if guide and guide["title"] not in guide_titles:
            guide_titles.append(guide["title"])

    detail = "Spaced repetition is ready now."
    if guide_titles:
        preview = ", ".join(guide_titles[:2])
        if len(guide_titles) > 2:
            preview += ", and more"
        detail = f"Clear recall work waiting across {preview}."

    return {
        "id": "review-queue",
        "task_type": "due_reviews",
        "title": f"Clear {review_count} review{'s' if review_count != 1 else ''}",
        "detail": detail,
        "cta_label": "Start review",
        "priority": 106 if review_count >= 5 else 96,
        "estimate_minutes": _estimate_task_minutes(review_count=review_count),
        "guide_id": None,
        "guide_title": None,
        "chapter_id": None,
        "chapter_title": None,
        "recommendation_type": None,
        "review_count": review_count,
        "signals": [],
        "matched_programs": [],
        "assessment": None,
    }


def _pick_applied_assessment_for_today(assessments: list[dict], reviews_due: int) -> dict | None:
    if not assessments:
        return None

    preferred_stages = (
        ["review", "scenario_practice"]
        if reviews_due > 0
        else [
            "scenario_practice",
            "review",
            "chapter_completion",
        ]
    )
    for stage in preferred_stages:
        for assessment in assessments:
            if assessment.get("stage") == stage:
                return assessment
    return assessments[0]


def _build_applied_practice_task(recommendation: dict, reviews_due: int) -> dict | None:
    if recommendation.get("recommendation_type") not in {"continue", "enrolled"}:
        return None

    guide_id = recommendation.get("guide_id")
    if not guide_id:
        return None

    assessment = _pick_applied_assessment_for_today(
        recommendation.get("applied_assessments", []),
        reviews_due,
    )
    if not assessment:
        return None

    has_draft = bool(assessment.get("draft_entry_path"))
    needs_revision = assessment.get("draft_status") == "active"
    has_submitted = assessment.get("draft_status") == "submitted"
    if needs_revision:
        title = f"Revise {assessment['title']}"
        detail = assessment.get("draft_feedback", {}).get("feedback") or assessment["summary"]
        cta_label = "Revise draft"
        priority = 101
    elif has_draft or has_submitted:
        title = f"{'Review' if has_submitted else 'Continue'} {assessment['title']}"
        detail = (
            f"Draft already created in Journal. {assessment['summary']}"
            if has_draft
            else assessment.get("draft_feedback", {}).get("feedback") or assessment["summary"]
        )
        cta_label = "Open draft"
        priority = 90 if has_submitted else 92
    else:
        title = assessment["title"]
        detail = assessment["summary"]
        cta_label = "Open guide"
        priority = 68
    return {
        "id": f"applied:{guide_id}:{assessment['type']}",
        "task_type": "applied_practice",
        "title": title,
        "detail": detail,
        "cta_label": cta_label,
        "priority": priority,
        "estimate_minutes": _estimate_task_minutes(assessment=assessment),
        "guide_id": guide_id,
        "guide_title": recommendation.get("guide_title"),
        "chapter_id": recommendation.get("chapter", {}).get("id")
        if recommendation.get("chapter")
        else None,
        "chapter_title": recommendation.get("chapter", {}).get("title")
        if recommendation.get("chapter")
        else None,
        "entry_path": assessment.get("draft_entry_path"),
        "recommendation_type": recommendation.get("recommendation_type"),
        "signals": [],
        "matched_programs": recommendation.get("matched_programs", []),
        "assessment": assessment,
    }


def _build_program_focus(
    store: CurriculumStore,
    user_id: str,
    program: dict,
    *,
    matched_program_ids: set[str],
    ready_guide_ids: set[str],
    learning_signal_map: dict[str, dict],
) -> dict | None:
    guide_ids = list(
        dict.fromkeys([*program.get("guide_ids", []), *program.get("applied_module_ids", [])])
    )
    if not guide_ids:
        return None

    total = 0
    enrolled = 0
    completed = 0
    in_progress = 0
    ready = 0
    weak_review_count = 0
    revision_backlog_count = 0
    submitted_assessment_count = 0
    assessment_grade_total = 0.0
    assessment_grade_count = 0
    for guide_id in guide_ids:
        guide = store.get_guide(guide_id, user_id=user_id) or store.get_guide(guide_id)
        if not guide:
            continue
        total += 1
        if guide.get("enrolled"):
            enrolled += 1
        if guide.get("enrollment_completed_at"):
            completed += 1
        elif (guide.get("progress_pct") or 0) > 0:
            in_progress += 1
        if guide_id in ready_guide_ids and not guide.get("enrolled"):
            ready += 1
        learning_signals = _guide_learning_signals(learning_signal_map, guide_id)
        weak_review_count += learning_signals["weak_review_count"]
        revision_backlog_count += learning_signals["revision_backlog_count"]
        submitted_assessment_count += learning_signals["submitted_assessment_count"]
        if (
            learning_signals["average_assessment_grade"] is not None
            and learning_signals["assessment_grade_count"]
        ):
            assessment_grade_total += (
                learning_signals["average_assessment_grade"]
                * learning_signals["assessment_grade_count"]
            )
            assessment_grade_count += learning_signals["assessment_grade_count"]

    if total == 0:
        return None

    has_active_work = in_progress > 0 or enrolled > completed
    if has_active_work:
        status = "active"
    elif program["id"] in matched_program_ids:
        status = "recommended"
    else:
        status = "available"

    return {
        **program,
        "status": status,
        "total_guide_count": total,
        "enrolled_guide_count": enrolled,
        "completed_guide_count": completed,
        "in_progress_guide_count": in_progress,
        "ready_guide_count": ready,
        "weak_review_count": weak_review_count,
        "revision_backlog_count": revision_backlog_count,
        "submitted_assessment_count": submitted_assessment_count,
        "average_assessment_grade": round(assessment_grade_total / assessment_grade_count, 1)
        if assessment_grade_count > 0
        else None,
        "progress_pct": round(completed / total * 100, 1),
    }


def _build_learning_today(
    user_id: str,
    store: CurriculumStore,
    scanner: CurriculumScanner,
    guide_aliases: set[str],
) -> dict:
    review_queue_count = store.count_review_queue(user_id)
    recommendation = _get_next_recommendation_v2(user_id, store, scanner, guide_aliases)
    learning_signal_map = _build_learning_signal_map(user_id, store)
    assessment_drafts = _list_assessment_drafts(user_id)
    if recommendation.get("guide_id"):
        recommendation["applied_assessments"] = _attach_assessment_drafts(
            recommendation["guide_id"],
            recommendation.get("applied_assessments", []),
            assessment_drafts,
        )
    ready_guides = store.get_ready_guides(user_id, excluded_guide_ids=guide_aliases)
    ready_guide_ids = {guide["id"] for guide in ready_guides}
    matched_program_ids = {program["id"] for program in recommendation.get("matched_programs", [])}

    tasks: list[dict] = []
    recommendation_task = _build_today_task_from_recommendation(recommendation, store, user_id)
    if recommendation_task:
        tasks.append(recommendation_task)

    review_task = _build_review_task(store, user_id, review_queue_count)
    if review_task:
        tasks.append(review_task)

    applied_task = _build_applied_practice_task(recommendation, review_queue_count)
    if applied_task:
        tasks.append(applied_task)

    deduped_tasks: list[dict] = []
    seen_task_ids: set[str] = set()
    for task in sorted(tasks, key=lambda item: (-item["priority"], item["title"])):
        if task["id"] in seen_task_ids:
            continue
        deduped_tasks.append(task)
        seen_task_ids.add(task["id"])

    focus_programs = []
    for program in scanner.get_learning_programs():
        focus = _build_program_focus(
            store,
            user_id,
            program,
            matched_program_ids=matched_program_ids,
            ready_guide_ids=ready_guide_ids,
            learning_signal_map=learning_signal_map,
        )
        if not focus:
            continue
        if (
            focus["status"] == "active"
            or focus["status"] == "recommended"
            or focus["ready_guide_count"] > 0
        ):
            focus_programs.append(focus)

    if not focus_programs:
        for program in scanner.get_learning_programs()[:3]:
            focus = _build_program_focus(
                store,
                user_id,
                program,
                matched_program_ids=matched_program_ids,
                ready_guide_ids=ready_guide_ids,
                learning_signal_map=learning_signal_map,
            )
            if focus:
                focus_programs.append(focus)

    status_rank = {"active": 0, "recommended": 1, "available": 2}
    focus_programs.sort(
        key=lambda item: (
            status_rank.get(item["status"], 9),
            -item["revision_backlog_count"],
            -item["weak_review_count"],
            -item["progress_pct"],
            -item["ready_guide_count"],
            item["title"],
        )
    )

    summary_parts = []
    if recommendation_task:
        summary_parts.append(recommendation_task["title"])
    if review_queue_count > 0:
        summary_parts.append(
            f"{review_queue_count} review{'s' if review_queue_count != 1 else ''} waiting"
        )
    active_program_count = sum(1 for program in focus_programs if program["status"] == "active")
    if active_program_count > 0:
        summary_parts.append(
            f"{active_program_count} active path{'s' if active_program_count != 1 else ''}"
        )

    if summary_parts:
        summary = "Today: " + " • ".join(summary_parts[:3])
    else:
        summary = "Choose a guide to start building momentum in Learn."

    return {
        "headline": "Today in Learn",
        "summary": summary,
        "recommended_action": recommendation if recommendation.get("guide_id") else None,
        "tasks": deduped_tasks[:4],
        "focus_programs": focus_programs[:3],
        "reviews_due": review_queue_count,
    }


def _chapter_content_path(chapter_id: str, user_id: str | None = None) -> Path | None:
    """Resolve chapter markdown file from content dirs.

    chapter_id format: guide_id/chapter_stem
    """
    return resolve_chapter_content_path(_content_dirs(user_id), chapter_id)


def _load_chapter_document(
    chapter_id: str, filename: str | None = None, *, user_id: str | None = None
):
    content_path = resolve_chapter_content_path(
        _content_dirs(user_id), chapter_id, filename=filename
    )
    if not content_path:
        return None, None
    return content_path, load_curriculum_document(content_path)


def _attach_guide_synthesis(guide: dict) -> dict:
    source_dir = str(guide.get("source_dir") or "").strip()
    guide_metadata = load_guide_metadata(Path(source_dir)) if source_dir else {}
    synthesis = derive_guide_synthesis(
        guide_title=str(guide.get("title") or ""),
        guide_summary=str(guide.get("summary") or ""),
        chapters=guide.get("chapters", []),
        raw_value=guide_metadata.get("synthesis"),
    )
    if synthesis:
        guide["guide_synthesis"] = synthesis.model_dump()
    return guide


def _attach_chapter_learning_aids(chapter: dict, document) -> dict:
    causal_lens = derive_causal_lens(document)
    misconception_card = derive_misconception_card(document)
    if causal_lens:
        chapter["causal_lens"] = causal_lens.model_dump()
    if misconception_card:
        chapter["misconception_card"] = misconception_card.model_dump()
    return chapter


# --- Endpoints ---


@router.get("/tracks")
async def list_tracks(
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    track_meta = scanner.get_track_metadata()
    guide_aliases = set(scanner.get_guide_aliases())
    if not track_meta:
        return []
    return store.list_tracks(user_id, track_meta, excluded_guide_ids=guide_aliases)


@router.get("/tree")
async def get_skill_tree(
    user: dict = Depends(get_current_user),
):
    """Return full DAG: tracks, nodes with layout positions, edges."""
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    guide_aliases = set(scanner.get_guide_aliases())

    track_meta = scanner.get_track_metadata()
    skill_tree = scanner._skill_tree
    positions = build_tree_layout(skill_tree)

    logger.info(
        "curriculum.tree_metadata",
        user_id=user_id,
        track_count=len(track_meta),
        track_ids=list(track_meta.keys()),
    )

    tree_data = store.get_tree_data(user_id, excluded_guide_ids=guide_aliases)
    track_payload = {
        track["id"]: track
        for track in store.list_tracks(user_id, track_meta, excluded_guide_ids=guide_aliases)
    }

    from curriculum.models import LearningProgram, SkillTreeEdge, SkillTreeNode, SkillTreeResponse

    nodes = []
    edges = []
    for g in tree_data:
        prereqs = g["prerequisites"]
        is_entry = len(prereqs) == 0
        pos = positions.get(g["id"], {"x": 0, "y": 0, "depth": 0})

        nodes.append(
            SkillTreeNode(
                id=g["id"],
                title=g["title"],
                track=g["track"],
                category=g["category"],
                difficulty=g["difficulty"],
                chapter_count=g["chapter_count"],
                prerequisites=prereqs,
                is_entry_point=is_entry,
                status=g["status"],
                enrolled=g["enrolled"],
                progress_pct=g["progress_pct"],
                mastery_score=g["mastery_score"],
                chapters_completed=g["chapters_completed"],
                chapters_total=g["chapters_total"],
                position=pos,
            )
        )
        for prereq_id in prereqs:
            edges.append(SkillTreeEdge(source=prereq_id, target=g["id"]))

    programs = [LearningProgram(**program) for program in scanner.get_learning_programs()]
    return SkillTreeResponse(tracks=track_payload, programs=programs, nodes=nodes, edges=edges)


@router.get("/guides")
async def list_guides(
    category: str | None = Query(None),
    origin: str | None = Query(None),
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    guide_aliases = set(scanner.get_guide_aliases())
    program_lookup = _build_program_lookup(scanner.get_learning_programs())

    guides = store.list_guides(category=category, user_id=user_id, origin=origin)
    visible_guides = [
        guide for guide in guides if guide["id"] not in guide_aliases or guide.get("enrolled")
    ]
    return [
        _decorate_guide_payload(guide, scanner, program_lookup, store=store, user_id=user_id)
        for guide in visible_guides
    ]


@router.get("/guides/archived")
async def list_archived_guides(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    program_lookup = _build_program_lookup(scanner.get_learning_programs())
    guides = store.list_archived_guides(user_id=user_id)
    return [
        _decorate_guide_payload(
            guide,
            scanner,
            program_lookup,
            store=store,
            user_id=user_id,
        )
        for guide in guides
    ]


@router.post("/guides/generate", status_code=status.HTTP_201_CREATED)
async def generate_user_guide(
    body: GuideGenerationRequest,
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    config = get_config()
    if len(body.topic.strip()) > config.curriculum.user_guide_max_topic_length:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Topic must be at most {config.curriculum.user_guide_max_topic_length} characters."
            ),
        )

    service = _build_guide_generation_service(user_id)
    store = _get_store(user_id)
    try:
        artifact = await service.generate_guide(
            topic=body.topic.strip(),
            depth=body.depth,
            audience=body.audience.strip(),
            time_budget=body.time_budget.strip(),
            instruction=body.instruction.strip() if body.instruction else None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("curriculum.user_guide_generation_failed", user_id=user_id)
        raise HTTPException(status_code=500, detail=f"Guide generation failed: {exc}") from exc

    scanner = _get_scanner(user_id, store)
    _sync_catalog(store, user_id=user_id, scanner=scanner)
    program_lookup = _build_program_lookup(scanner.get_learning_programs())
    created_guide = store.get_guide(artifact["guide_id"], user_id=user_id)
    if not created_guide:
        raise HTTPException(status_code=500, detail="Generated guide was not available after sync.")

    log_event("curriculum_user_guide_created", user_id, {"guide_id": artifact["guide_id"]})
    return _decorate_guide_payload(
        created_guide,
        scanner,
        program_lookup,
        store=store,
        user_id=user_id,
    )


@router.post("/guides/{guide_id}/extend", status_code=status.HTTP_201_CREATED)
async def extend_guide(
    guide_id: str,
    body: GuideExtensionRequest,
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    resolved_guide_id = _resolve_guide_id(scanner, guide_id)
    source_guide = store.get_guide(resolved_guide_id, user_id=user_id)
    if not source_guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    service = _build_guide_generation_service(user_id)
    try:
        artifact = await service.extend_guide(
            source_guide=source_guide,
            prompt=body.prompt.strip(),
            depth=body.depth,
            audience=body.audience.strip() if body.audience else None,
            time_budget=body.time_budget.strip() if body.time_budget else None,
            instruction=body.instruction.strip() if body.instruction else None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "curriculum.user_guide_extension_failed",
            user_id=user_id,
            guide_id=resolved_guide_id,
        )
        raise HTTPException(status_code=500, detail=f"Guide extension failed: {exc}") from exc

    _sync_catalog(store, user_id=user_id, scanner=scanner)
    program_lookup = _build_program_lookup(scanner.get_learning_programs())
    created_guide = store.get_guide(artifact["guide_id"], user_id=user_id)
    if not created_guide:
        raise HTTPException(
            status_code=500, detail="Generated extension was not available after sync."
        )

    log_event(
        "curriculum_user_guide_extended",
        user_id,
        {"guide_id": artifact["guide_id"], "base_guide_id": resolved_guide_id},
    )
    return _decorate_guide_payload(
        created_guide,
        scanner,
        program_lookup,
        store=store,
        user_id=user_id,
    )


@router.delete("/guides/{guide_id}")
async def archive_user_guide(
    guide_id: str,
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    resolved_guide_id = _resolve_guide_id(scanner, guide_id)
    guide = store.get_guide(resolved_guide_id, user_id=user_id)
    if not guide:
        guide = store.get_guide(resolved_guide_id, user_id=user_id, include_archived=True)
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    _ensure_user_guide_mutable(guide)

    active_dir, archive_dir = ensure_user_curriculum_dirs(user_id)
    source_dir = Path(guide["source_dir"])
    target_dir = archive_dir / resolved_guide_id
    if guide.get("archived_at"):
        raise HTTPException(status_code=409, detail="Guide is already archived.")
    if not source_dir.exists():
        raise HTTPException(status_code=404, detail="Guide content directory not found.")
    if target_dir.exists():
        raise HTTPException(status_code=409, detail="Archived guide path already exists.")

    shutil.move(str(source_dir), str(target_dir))
    store.archive_guide(resolved_guide_id, str(target_dir))
    log_event("curriculum_user_guide_archived", user_id, {"guide_id": resolved_guide_id})
    return {"archived": True, "guide_id": resolved_guide_id}


@router.post("/guides/{guide_id}/restore")
async def restore_user_guide(
    guide_id: str,
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    resolved_guide_id = _resolve_guide_id(scanner, guide_id)
    guide = store.get_guide(resolved_guide_id, user_id=user_id, include_archived=True)
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    if guide.get("origin") != "user":
        raise HTTPException(status_code=403, detail="Built-in guides cannot be restored.")
    if not guide.get("archived_at"):
        raise HTTPException(status_code=409, detail="Guide is not archived.")

    active_dir, _ = ensure_user_curriculum_dirs(user_id)
    source_dir = Path(guide.get("archive_path") or "")
    target_dir = active_dir / resolved_guide_id
    if not source_dir.exists():
        raise HTTPException(status_code=404, detail="Archived guide content directory not found.")
    if target_dir.exists():
        raise HTTPException(status_code=409, detail="Active guide path already exists.")

    shutil.move(str(source_dir), str(target_dir))
    store.restore_guide(resolved_guide_id)
    _sync_catalog(store, user_id=user_id, scanner=scanner)
    log_event("curriculum_user_guide_restored", user_id, {"guide_id": resolved_guide_id})
    return {"restored": True, "guide_id": resolved_guide_id}


@router.get("/guides/{guide_id}", response_model=CurriculumGuideDetailResponse)
async def get_guide(
    guide_id: str,
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    resolved_guide_id = _resolve_guide_id(scanner, guide_id)
    program_lookup = _build_program_lookup(scanner.get_learning_programs())
    profile = _load_user_profile(user_id)
    guide = store.get_guide(resolved_guide_id, user_id=user_id)
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    next_chapter = store.get_next_chapter(user_id, resolved_guide_id)
    payload = _decorate_guide_payload(
        guide,
        scanner,
        program_lookup,
        store=store,
        user_id=user_id,
        profile=profile,
        include_applied_assessments=True,
        assessment_chapter_title=next_chapter["title"] if next_chapter else None,
    )
    payload["applied_assessments"] = _attach_assessment_drafts(
        payload["id"],
        payload.get("applied_assessments", []),
        _list_assessment_drafts(user_id, guide_id=payload["id"]),
    )
    return _attach_guide_synthesis(payload)


@router.get(
    "/guides/{guide_id}/chapters/{chapter_id:path}",
    response_model=CurriculumChapterDetailResponse,
)
async def get_chapter(
    guide_id: str,
    chapter_id: str,
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    resolved_guide_id = _resolve_guide_id(scanner, guide_id)

    # chapter_id comes in as the part after guide_id, reconstruct full id
    full_chapter_id = f"{resolved_guide_id}/{chapter_id}"
    chapter = store.get_chapter(full_chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Read content
    _, document = _load_chapter_document(full_chapter_id, chapter.get("filename"), user_id=user_id)
    if not document:
        raise HTTPException(status_code=404, detail="Chapter content file not found")

    # Get progress
    progress = store.get_chapter_progress(user_id, full_chapter_id)

    # Compute prev/next
    guide = store.get_guide(resolved_guide_id, user_id=user_id)
    prev_chapter = None
    next_chapter = None
    if guide and guide.get("chapters"):
        chapters_list = guide["chapters"]
        for i, ch in enumerate(chapters_list):
            if ch["id"] == full_chapter_id:
                if i > 0:
                    prev_chapter = chapters_list[i - 1]["id"]
                if i < len(chapters_list) - 1:
                    next_chapter = chapters_list[i + 1]["id"]
                break

    payload = {
        **chapter,
        "content": document.body,
        "progress": progress,
        "prev_chapter": prev_chapter,
        "next_chapter": next_chapter,
    }
    return _attach_chapter_learning_aids(payload, document)


@router.post("/guides/{guide_id}/enroll", status_code=status.HTTP_201_CREATED)
async def enroll_guide(
    guide_id: str,
    create_goal: bool = Query(True),
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    resolved_guide_id = _resolve_guide_id(scanner, guide_id)
    guide = store.get_guide(resolved_guide_id, user_id=user_id)
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    store.enroll(user_id, resolved_guide_id)

    linked_goal_path: str | None = None
    milestones_added = 0

    if create_goal:
        try:
            from advisor.goals import GoalTracker, get_goal_defaults
            from journal.storage import JournalStorage

            paths = get_user_paths(user_id)
            journal_storage = JournalStorage(paths["journal_dir"])
            goal_path = journal_storage.create(
                content=f"Complete the **{guide['title']}** curriculum guide.",
                entry_type="goal",
                title=f"Learn: {guide['title']}",
                tags=["learning", "curriculum"],
                metadata=get_goal_defaults(goal_type="learning"),
            )
            linked_goal_path = str(goal_path)

            # Add chapter milestones
            tracker = GoalTracker(journal_storage)
            chapters = guide.get("chapters", [])
            for ch in chapters:
                if not ch.get("is_glossary"):
                    tracker.add_milestone(goal_path, ch["title"])
                    milestones_added += 1

            # Link goal back to enrollment
            store.enroll(user_id, resolved_guide_id, linked_goal_id=linked_goal_path)
        except Exception as exc:
            logger.warning("enroll_goal_creation_failed", guide=guide_id, error=str(exc))

    log_event("curriculum_enrolled", user_id, {"guide_id": resolved_guide_id})
    return {
        "status": "enrolled",
        "guide_id": resolved_guide_id,
        "linked_goal_path": linked_goal_path,
        "milestones_added": milestones_added,
    }


@router.post("/progress")
async def update_progress(
    body: ProgressUpdate,
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    resolved_guide_id = _resolve_guide_id(scanner, body.guide_id)
    resolved_chapter_id = _resolve_chapter_id(scanner, body.chapter_id)
    result = store.update_progress(
        user_id=user_id,
        chapter_id=resolved_chapter_id,
        guide_id=resolved_guide_id,
        status=body.status.value if body.status else None,
        reading_time_seconds=body.reading_time_seconds,
        scroll_position=body.scroll_position,
    )

    reflection_prompt: str | None = None
    memory_facts_extracted = 0

    if body.status == ChapterStatus.COMPLETED:
        log_event(
            "chapter_completed",
            user_id,
            {"chapter_id": resolved_chapter_id, "guide_id": resolved_guide_id},
        )

        # Reflection prompt
        try:
            chapter = store.get_chapter(resolved_chapter_id)
            ch_title = chapter["title"] if chapter else resolved_chapter_id
            guide = store.get_guide(resolved_guide_id)
            g_title = guide["title"] if guide else resolved_guide_id
            guide_complete = _is_guide_just_completed(store, user_id, resolved_guide_id)
            reflection_prompt = _generate_reflection_prompt(ch_title, g_title, guide_complete)
        except Exception as exc:
            logger.debug("reflection_prompt_failed", error=str(exc))

        # Memory extraction from chapter content
        try:
            config = get_config()
            if config.memory.enabled:
                _, document = _load_chapter_document(resolved_chapter_id, user_id=user_id)
                if document:
                    text = document.body[:3000]
                    from memory.pipeline import MemoryPipeline
                    from web.deps import get_memory_store

                    fact_store = get_memory_store(user_id)
                    pipeline = MemoryPipeline(fact_store)
                    updates = pipeline.process_document(
                        document_id=f"curriculum:{resolved_chapter_id}",
                        document_text=text,
                        document_metadata={
                            "source_type": "curriculum",
                            "guide_id": resolved_guide_id,
                            "chapter_id": resolved_chapter_id,
                        },
                    )
                    memory_facts_extracted = len(updates)
        except Exception as exc:
            logger.debug("curriculum_memory_extraction_failed", error=str(exc))

    teachback_available = False
    if body.status == ChapterStatus.COMPLETED:
        try:
            config = get_config()
            teachback_available = config.curriculum.teachback_enabled
        except Exception:
            pass

    return {
        **(result if isinstance(result, dict) else {"status": "updated"}),
        "reflection_prompt": reflection_prompt,
        "memory_facts_extracted": memory_facts_extracted,
        "teachback_available": teachback_available,
    }


def _generate_reflection_prompt(
    chapter_title: str, guide_title: str, is_guide_complete: bool
) -> str:
    if is_guide_complete:
        return (
            f"You finished '{guide_title}'. What's the most important concept "
            f"you learned and how might you apply it?"
        )
    return f"You completed '{chapter_title}'. What was the key takeaway?"


def _is_guide_just_completed(store: CurriculumStore, user_id: str, guide_id: str) -> bool:
    """Check if all non-glossary chapters are now completed."""
    guide = store.get_guide(guide_id, user_id=user_id)
    if not guide:
        return False
    chapters = guide.get("chapters", [])
    for ch in chapters:
        if ch.get("is_glossary"):
            continue
        prog = store.get_chapter_progress(user_id, ch["id"])
        if not prog or prog.get("status") != "completed":
            return False
    return True


@router.get("/review/due", response_model=list[CurriculumReviewItemResponse])
async def get_due_reviews(
    guide_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    return store.get_due_reviews(user["id"], limit=limit, guide_id=guide_id)


@router.get("/review/retry", response_model=list[CurriculumReviewItemResponse])
async def get_retry_reviews(
    guide_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    return store.get_retry_review_items(user["id"], limit=limit, guide_id=guide_id)


@router.post("/review/{review_id}/grade")
async def grade_review(
    review_id: str,
    body: ReviewGradeRequest,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    item = store.get_review_item(review_id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")

    # If self-grade provided, use it directly
    if body.self_grade is not None:
        grade = max(0, min(5, body.self_grade))
        grade_result = None
    else:
        # LLM grading
        try:
            gen = _build_question_generator(user["id"])
            if item.get("item_type") == ReviewItemType.TEACHBACK.value:
                concept = item["question"].removeprefix("Explain ").split(" as if ")[0]
                chapter = store.get_chapter(item["chapter_id"])
                guide = store.get_guide(item["guide_id"]) if chapter else None
                grade_result = await gen.grade_teachback(
                    concept=concept,
                    expected_answer=item["expected_answer"],
                    student_answer=body.answer,
                    chapter_title=chapter["title"] if chapter else "",
                    guide_title=guide["title"] if guide else "",
                )
            else:
                bloom = BloomLevel(item["bloom_level"])
                grade_result = await gen.grade_answer(
                    question=item["question"],
                    expected_answer=item["expected_answer"],
                    student_answer=body.answer,
                    bloom_level=bloom,
                )
            grade = grade_result.grade
        except Exception:
            grade = 3  # default if grading fails
            grade_result = None

    updated = store.grade_review(review_id, grade)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update review")

    log_event(
        "review_graded",
        user["id"],
        {
            "review_id": review_id,
            "grade": grade,
        },
    )
    response = {"review": updated, "grade": grade}
    if grade_result:
        response.update(
            {
                "feedback": grade_result.feedback,
                "correct_points": grade_result.correct_points,
                "missing_points": grade_result.missing_points,
            }
        )
    return response


@router.post("/quiz/{chapter_id:path}/generate")
async def generate_quiz(
    chapter_id: str,
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    resolved_chapter_id = _resolve_chapter_id(scanner, chapter_id)
    chapter = store.get_chapter(resolved_chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Check if questions already exist
    existing_artifacts = _load_current_cached_artifacts(
        store,
        user_id=user_id,
        chapter_id=resolved_chapter_id,
        content_hash=chapter["content_hash"],
        item_types={
            ReviewItemType.QUIZ.value,
            ReviewItemType.PREDICTION.value,
            ReviewItemType.PRE_READING.value,
        },
    )
    existing = [
        item
        for item in existing_artifacts
        if item.get("item_type") in {ReviewItemType.QUIZ.value, ReviewItemType.PREDICTION.value}
    ]
    if existing:
        return {"questions": existing, "cached": True}

    # Read content
    _, document = _load_chapter_document(
        resolved_chapter_id, chapter.get("filename"), user_id=user_id
    )
    if not document:
        raise HTTPException(status_code=404, detail="Chapter content not found")

    # Get guide title
    guide = store.get_guide(chapter["guide_id"])
    guide_title = guide["title"] if guide else ""

    gen = _build_question_generator(user["id"])
    items = await gen.generate_questions(
        content=document.body,
        chapter_title=chapter["title"],
        guide_title=guide_title,
        count=5,
        content_hash=chapter["content_hash"],
        chapter_id=resolved_chapter_id,
        guide_id=chapter["guide_id"],
        user_id=user["id"],
    )

    if items:
        store.add_review_items(items)

    quiz_items = [
        i.model_dump()
        for i in items
        if i.item_type in {ReviewItemType.QUIZ, ReviewItemType.PREDICTION}
    ]
    return {"questions": quiz_items, "cached": False}


@router.post("/quiz/{chapter_id:path}/submit")
async def submit_quiz(
    chapter_id: str,
    body: QuizSubmission,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    scanner = _get_scanner(user["id"], store)
    resolved_chapter_id = _resolve_chapter_id(scanner, chapter_id)
    results = []

    for question_id, answer in body.answers.items():
        item = store.get_review_item(question_id)
        if not item:
            continue

        gen = _build_question_generator(user["id"])
        bloom = BloomLevel(item["bloom_level"])
        grade_result = await gen.grade_answer(
            question=item["question"],
            expected_answer=item["expected_answer"],
            student_answer=answer,
            bloom_level=bloom,
        )

        store.grade_review(question_id, grade_result.grade)
        results.append(
            {
                "question_id": question_id,
                "grade": grade_result.grade,
                "feedback": grade_result.feedback,
                "correct_points": grade_result.correct_points,
                "missing_points": grade_result.missing_points,
            }
        )

    log_event(
        "quiz_completed",
        user["id"],
        {
            "chapter_id": resolved_chapter_id,
            "avg_grade": sum(r["grade"] for r in results) / len(results) if results else 0,
        },
    )
    return {"results": results}


@router.post("/teachback/{chapter_id:path}/generate")
async def generate_teachback(
    chapter_id: str,
    user: dict = Depends(get_current_user),
):
    """Generate a teach-back prompt for a completed chapter."""
    config = get_config()
    if not config.curriculum.teachback_enabled:
        raise HTTPException(status_code=400, detail="Teach-back disabled")

    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    resolved_chapter_id = _resolve_chapter_id(scanner, chapter_id)
    chapter = store.get_chapter(resolved_chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Must be completed
    progress = store.get_chapter_progress(user_id, resolved_chapter_id)
    if not progress or progress.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Chapter not completed")

    # Return cached
    existing_items = _load_current_cached_artifacts(
        store,
        user_id=user_id,
        chapter_id=resolved_chapter_id,
        content_hash=chapter["content_hash"],
        item_types={ReviewItemType.TEACHBACK.value},
    )
    existing = existing_items[0] if existing_items else None
    if existing:
        return {
            "concept": existing["question"].removeprefix("Explain ").split(" as if ")[0],
            "prompt": existing["question"],
            "review_item_id": existing["id"],
        }

    # Generate
    _, document = _load_chapter_document(
        resolved_chapter_id, chapter.get("filename"), user_id=user_id
    )
    if not document:
        raise HTTPException(status_code=404, detail="Chapter content not found")

    guide = store.get_guide(chapter["guide_id"])
    guide_title = guide["title"] if guide else ""

    gen = _build_question_generator(user_id)
    item = await gen.generate_teachback(
        content=document.body,
        chapter_title=chapter["title"],
        guide_title=guide_title,
        content_hash=chapter["content_hash"],
        chapter_id=resolved_chapter_id,
        guide_id=chapter["guide_id"],
        user_id=user_id,
    )

    if not item:
        raise HTTPException(status_code=500, detail="Failed to generate teach-back")

    store.add_review_items([item])
    return {
        "concept": item.question.removeprefix("Explain ").split(" as if ")[0],
        "prompt": item.question,
        "review_item_id": item.id,
    }


@router.post("/teachback/{review_id}/grade")
async def grade_teachback(
    review_id: str,
    body: ReviewGradeRequest,
    user: dict = Depends(get_current_user),
):
    """Grade a teach-back response."""
    user_id = user["id"]
    store = _get_store(user_id)
    item = store.get_review_item(review_id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    if item.get("item_type") != "teachback":
        raise HTTPException(status_code=400, detail="Not a teach-back item")

    # Extract concept from question
    concept = item["question"].removeprefix("Explain ").split(" as if ")[0]

    chapter = store.get_chapter(item["chapter_id"])
    guide = store.get_guide(item["guide_id"]) if chapter else None

    gen = _build_question_generator(user_id)
    result = await gen.grade_teachback(
        concept=concept,
        expected_answer=item["expected_answer"],
        student_answer=body.answer,
        chapter_title=chapter["title"] if chapter else "",
        guide_title=guide["title"] if guide else "",
    )

    # SM-2 scheduling
    store.grade_review(review_id, result.grade)

    log_event(
        "teachback_graded",
        user_id,
        {"review_id": review_id, "grade": result.grade},
    )
    return {
        "grade": result.grade,
        "feedback": result.feedback,
        "correct_points": result.correct_points,
        "missing_points": result.missing_points,
    }


@router.get("/chapters/{chapter_id:path}/pre-reading")
async def get_pre_reading(
    chapter_id: str,
    user: dict = Depends(get_current_user),
):
    """Get or generate pre-reading priming questions for a chapter."""
    config = get_config()
    if not config.curriculum.pre_reading_enabled:
        return {"questions": []}

    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    resolved_chapter_id = _resolve_chapter_id(scanner, chapter_id)
    chapter = store.get_chapter(resolved_chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Return cached
    existing_artifacts = _load_current_cached_artifacts(
        store,
        user_id=user_id,
        chapter_id=resolved_chapter_id,
        content_hash=chapter["content_hash"],
        item_types={
            ReviewItemType.QUIZ.value,
            ReviewItemType.PREDICTION.value,
            ReviewItemType.PRE_READING.value,
        },
    )
    existing = [
        item
        for item in existing_artifacts
        if item.get("item_type") == ReviewItemType.PRE_READING.value
    ]
    if existing:
        return {"questions": existing}

    # Generate (includes both quiz + pre-reading items)
    _, document = _load_chapter_document(
        resolved_chapter_id, chapter.get("filename"), user_id=user_id
    )
    if not document:
        return {"questions": []}

    guide = store.get_guide(chapter["guide_id"])
    guide_title = guide["title"] if guide else ""

    gen = _build_question_generator(user_id)
    items = await gen.generate_questions(
        content=document.body,
        chapter_title=chapter["title"],
        guide_title=guide_title,
        count=config.curriculum.questions_per_chapter,
        content_hash=chapter["content_hash"],
        chapter_id=resolved_chapter_id,
        guide_id=chapter["guide_id"],
        user_id=user_id,
        include_pre_reading=True,
        pre_reading_count=config.curriculum.pre_reading_count,
    )

    if any(
        item.get("item_type") in {ReviewItemType.QUIZ.value, ReviewItemType.PREDICTION.value}
        for item in existing_artifacts
    ):
        items = [
            item
            for item in items
            if item.item_type not in {ReviewItemType.QUIZ, ReviewItemType.PREDICTION}
        ]

    if items:
        store.add_review_items(items)

    pre_reading = [i.model_dump() for i in items if i.item_type == ReviewItemType.PRE_READING]
    return {"questions": pre_reading}


@router.get("/chapters/{chapter_id:path}/related")
async def get_related_chapters(
    chapter_id: str,
    limit: int = Query(3, ge=1, le=10),
    user: dict = Depends(get_current_user),
):
    """Find related chapters from other enrolled guides."""
    config = get_config()
    if not config.curriculum.cross_guide_connections:
        return {"related": []}

    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    resolved_chapter_id = _resolve_chapter_id(scanner, chapter_id)
    chapter = store.get_chapter(resolved_chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Get enrolled guide IDs
    enrollments = store.get_enrollments(user_id)
    enrolled_ids = [e["guide_id"] for e in enrollments]
    if len(enrolled_ids) < 2:
        return {"related": []}

    # Read current chapter content
    _, document = _load_chapter_document(
        resolved_chapter_id, chapter.get("filename"), user_id=user_id
    )
    if not document:
        return {"related": []}

    try:
        emb = _get_chapter_embeddings(user_id, store)
        results = emb.find_related(
            chapter_content=document.body,
            current_guide_id=chapter["guide_id"],
            enrolled_guide_ids=enrolled_ids,
            n_results=limit,
        )

        # Enrich with guide titles
        for r in results:
            guide = store.get_guide(r["guide_id"])
            r["guide_title"] = guide["title"] if guide else r["guide_id"]

        return {"related": results}
    except Exception:
        logger.exception("related_chapters_failed")
        return {"related": []}


def _get_chapter_embeddings(user_id: str, store: CurriculumStore):
    """Lazy-init chapter embeddings, syncing all chapters if empty."""
    from curriculum.embeddings import ChapterEmbeddingManager

    paths = get_user_paths(user_id)
    chroma_dir = Path(paths["data_dir"]) / "chroma"
    emb = ChapterEmbeddingManager(chroma_dir)

    if emb.count() == 0:
        # Bulk sync all chapters
        all_guides = store.list_guides()
        all_chapters = []
        for g in all_guides:
            guide_detail = store.get_guide(g["id"])
            if guide_detail and guide_detail.get("chapters"):
                all_chapters.extend(guide_detail["chapters"])

        def reader(ch_id: str) -> str | None:
            chapter = store.get_chapter(ch_id)
            if not chapter:
                return None
            _, document = _load_chapter_document(ch_id, chapter.get("filename"), user_id=user_id)
            return document.body if document else None

        emb.sync_from_chapters(all_chapters, reader)

    return emb


@router.get("/stats")
async def get_stats(user: dict = Depends(get_current_user)):
    store = _get_store(user["id"])
    _ensure_catalog_initialized(store, user_id=user["id"])
    stats = store.get_stats(user["id"])
    return stats.model_dump()


@router.get("/today")
async def get_today_learning_workflow(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    guide_aliases = set(scanner.get_guide_aliases())
    return _build_learning_today(user_id, store, scanner, guide_aliases)


@router.post("/sync")
async def sync_content(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    store = _get_store(user_id)
    count = _sync_catalog(store, user_id=user_id)
    logger.info("curriculum.sync_completed", user_id=user_id, guide_count=count)
    return {"synced_guides": count, "message": f"Synced {count} guides with latest track data"}


@router.get("/ready")
async def get_ready_guides(
    user: dict = Depends(get_current_user),
):
    """Return guides whose prerequisites are all completed but not yet enrolled."""
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    guide_aliases = set(scanner.get_guide_aliases())
    program_lookup = _build_program_lookup(scanner.get_learning_programs())
    ready_guides = store.get_ready_guides(user_id, excluded_guide_ids=guide_aliases)
    return [
        _decorate_guide_payload(guide, scanner, program_lookup, store=store, user_id=user_id)
        for guide in ready_guides
    ]


@router.get("/next")
async def get_next_recommendation(
    user: dict = Depends(get_current_user),
):
    """Get advisor-recommended next chapter/guide to study (DAG-aware)."""
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    guide_aliases = set(scanner.get_guide_aliases())
    return _get_next_recommendation_v2(user_id, store, scanner, guide_aliases)


@router.post(
    "/guides/{guide_id}/assessments/{assessment_type}/launch", status_code=status.HTTP_201_CREATED
)
async def launch_applied_assessment(
    guide_id: str,
    assessment_type: str,
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    resolved_guide_id = _resolve_guide_id(scanner, guide_id)
    guide, assessment = _get_applied_assessment_definition(
        user_id=user_id,
        store=store,
        scanner=scanner,
        guide_id=resolved_guide_id,
        assessment_type=assessment_type,
    )

    existing_draft = _get_applied_assessment_artifact(
        user_id,
        guide_id=resolved_guide_id,
        assessment_type=assessment_type,
    )
    if existing_draft:
        return {
            "guide_id": resolved_guide_id,
            "assessment_type": assessment_type,
            "entry_path": existing_draft["entry_path"],
            "entry_title": existing_draft["entry_title"],
            "goal_path": existing_draft.get("goal_path"),
            "goal_title": existing_draft.get("goal_title"),
            "created": False,
        }

    from advisor.goals import GoalTracker, get_goal_defaults
    from journal.storage import JournalStorage

    storage = JournalStorage(get_user_paths(user_id)["journal_dir"])
    tags = [
        "learning",
        "assessment",
        resolved_guide_id,
        assessment_type.replace("_", "-"),
    ]

    goal_title = f"Apply {guide['title']}: {assessment['title']}"
    goal_path = storage.create(
        content=_build_assessment_goal_content(guide, assessment),
        entry_type="goal",
        title=goal_title,
        tags=tags,
        metadata={
            **get_goal_defaults(goal_type="learning"),
            "curriculum_guide_id": resolved_guide_id,
            "curriculum_guide_title": guide["title"],
            "curriculum_assessment_type": assessment_type,
            "curriculum_assessment_stage": assessment["stage"],
            "assessment_status": "active",
        },
    )

    tracker = GoalTracker(storage)
    for milestone in ["Draft response", "Review against rubric", "Finalize deliverable"]:
        tracker.add_milestone(goal_path, milestone)

    entry_title = f"{guide['title']} - {assessment['title']}"
    entry_path = storage.create(
        content=_build_assessment_entry_content(guide, assessment),
        entry_type=_assessment_entry_type(assessment_type),
        title=entry_title,
        tags=tags,
        metadata={
            "curriculum_guide_id": resolved_guide_id,
            "curriculum_guide_title": guide["title"],
            "curriculum_assessment_type": assessment_type,
            "curriculum_assessment_stage": assessment["stage"],
            "assessment_status": "draft",
            "linked_goal_path": str(goal_path),
            "linked_goal_title": goal_title,
        },
    )
    _schedule_curriculum_entry_hooks(user_id, entry_path, storage)

    log_event(
        "curriculum_assessment_launched",
        user_id,
        {
            "guide_id": resolved_guide_id,
            "assessment_type": assessment_type,
            "entry_path": str(entry_path),
            "goal_path": str(goal_path),
        },
    )
    return {
        "guide_id": resolved_guide_id,
        "assessment_type": assessment_type,
        "entry_path": str(entry_path),
        "entry_title": entry_title,
        "goal_path": str(goal_path),
        "goal_title": goal_title,
        "created": True,
    }


@router.post("/guides/{guide_id}/assessments/{assessment_type}/submit")
async def submit_applied_assessment(
    guide_id: str,
    assessment_type: str,
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    resolved_guide_id = _resolve_guide_id(scanner, guide_id)
    guide, assessment = _get_applied_assessment_definition(
        user_id=user_id,
        store=store,
        scanner=scanner,
        guide_id=resolved_guide_id,
        assessment_type=assessment_type,
    )
    artifact = _get_applied_assessment_artifact(
        user_id,
        guide_id=resolved_guide_id,
        assessment_type=assessment_type,
    )
    if not artifact:
        raise HTTPException(status_code=404, detail="Assessment draft not found")

    from journal.storage import JournalStorage

    storage = JournalStorage(get_user_paths(user_id)["journal_dir"])
    post = storage.read(artifact["entry_path"])
    submission = (post.content or "").strip()
    if len(submission.split()) < 20:
        raise HTTPException(
            status_code=400,
            detail="Add more substance to the draft before submitting it for feedback",
        )

    gen = _build_question_generator(user_id)
    grade_result = await gen.grade_applied_assessment(
        guide_title=guide["title"],
        assessment_type=assessment_type,
        assessment_prompt=assessment["prompt"],
        evaluation_focus=assessment["evaluation_focus"],
        student_answer=submission,
    )
    feedback = _format_assessment_feedback(grade_result.model_dump())
    next_status = "submitted" if grade_result.grade >= 4 else "active"

    metadata = {
        "assessment_status": next_status,
        "assessment_feedback": feedback,
    }
    storage.update(artifact["entry_path"], metadata=metadata)

    goal_path = artifact.get("goal_path")
    for milestone_index in (0, 1):
        _complete_goal_milestone_if_present(goal_path, milestone_index, user_id)
    if next_status == "submitted":
        _complete_goal_milestone_if_present(goal_path, 2, user_id)
        _update_goal_status_if_present(goal_path, "completed", user_id)
    else:
        _update_goal_status_if_present(goal_path, "active", user_id)

    log_event(
        "curriculum_assessment_submitted",
        user_id,
        {
            "guide_id": resolved_guide_id,
            "assessment_type": assessment_type,
            "entry_path": artifact["entry_path"],
            "goal_path": goal_path,
            "grade": grade_result.grade,
            "status": next_status,
        },
    )
    return {
        "guide_id": resolved_guide_id,
        "assessment_type": assessment_type,
        "entry_path": artifact["entry_path"],
        "goal_path": goal_path,
        "status": next_status,
        **feedback,
    }


# --- Placement bypass (test-out) ---

_placement_cache: dict[tuple[str, str], dict] = {}
_PLACEMENT_TTL = timedelta(hours=1)


@router.post("/guides/{guide_id}/placement/generate")
async def generate_placement(
    guide_id: str,
    user: dict = Depends(get_current_user),
):
    """Generate placement quiz for testing out of a guide."""
    config = get_config()
    if not config.curriculum.placement_enabled:
        raise HTTPException(status_code=400, detail="Placement bypass disabled")

    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _get_scanner(user_id, store)
    resolved_guide_id = _resolve_guide_id(scanner, guide_id)
    guide = store.get_guide(resolved_guide_id, user_id=user_id)
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    # Reject if already completed
    if guide.get("enrollment_completed_at"):
        raise HTTPException(status_code=400, detail="Guide already completed")

    chapters = [c for c in guide.get("chapters", []) if not c.get("is_glossary")]
    if not chapters:
        raise HTTPException(status_code=400, detail="No assessable chapters")

    gen = _build_question_generator(user_id)
    all_questions: list[dict] = []
    max_q = config.curriculum.placement_max_questions
    per_ch = config.curriculum.placement_questions_per_chapter

    for ch in chapters:
        if len(all_questions) >= max_q:
            break
        _, document = _load_chapter_document(ch["id"], ch.get("filename"), user_id=user_id)
        if not document:
            continue
        guide_title = guide["title"]
        remaining = max_q - len(all_questions)
        count = min(per_ch, remaining)

        questions = await gen.generate_placement_questions(
            content=document.body,
            chapter_title=ch["title"],
            guide_title=guide_title,
            count=count,
        )
        for q in questions:
            q["chapter_id"] = ch["id"]
        all_questions.extend(questions)

    if not all_questions:
        raise HTTPException(status_code=500, detail="Failed to generate placement questions")

    # Cache with answers server-side
    _placement_cache[(user_id, resolved_guide_id)] = {
        "questions": all_questions,
        "created_at": datetime.utcnow(),
    }

    # Return without expected_answer
    client_questions = [
        {
            "id": q["id"],
            "chapter_id": q.get("chapter_id", ""),
            "question": q["question"],
            "bloom_level": q.get("bloom_level", "apply"),
        }
        for q in all_questions
    ]

    log_event(
        "placement_generated",
        user_id,
        {"guide_id": resolved_guide_id, "count": len(client_questions)},
    )
    return {"questions": client_questions, "guide_id": resolved_guide_id}


@router.post("/guides/{guide_id}/placement/submit")
async def submit_placement(
    guide_id: str,
    body: QuizSubmission,
    user: dict = Depends(get_current_user),
):
    """Submit placement answers and grade them."""
    config = get_config()
    user_id = user["id"]
    scanner = CurriculumScanner(_content_dirs(user_id))
    resolved_guide_id = _resolve_guide_id(scanner, guide_id)

    cache_key = (user_id, resolved_guide_id)
    cached = _placement_cache.get(cache_key)
    if not cached:
        raise HTTPException(status_code=410, detail="Placement session expired or not found")

    if datetime.utcnow() - cached["created_at"] > _PLACEMENT_TTL:
        _placement_cache.pop(cache_key, None)
        raise HTTPException(status_code=410, detail="Placement session expired")

    questions_by_id = {q["id"]: q for q in cached["questions"]}
    gen = _build_question_generator(user_id)
    results = []

    for question_id, answer in body.answers.items():
        q = questions_by_id.get(question_id)
        if not q:
            continue
        bloom_str = q.get("bloom_level", "apply")
        try:
            bloom = BloomLevel(bloom_str)
        except ValueError:
            bloom = BloomLevel.APPLY

        grade_result = await gen.grade_answer(
            question=q["question"],
            expected_answer=q.get("expected_answer", ""),
            student_answer=answer,
            bloom_level=bloom,
        )
        results.append(
            {
                "question_id": question_id,
                "grade": grade_result.grade,
                "feedback": grade_result.feedback,
                "correct_points": grade_result.correct_points,
                "missing_points": grade_result.missing_points,
            }
        )

    avg_grade = sum(r["grade"] for r in results) / len(results) if results else 0
    threshold = config.curriculum.placement_pass_threshold
    passed = avg_grade >= threshold

    completion = None
    if passed:
        store = _get_store(user_id)
        completion = store.complete_guide_placement(user_id, resolved_guide_id)
        _placement_cache.pop(cache_key, None)
        log_event(
            "placement_passed",
            user_id,
            {"guide_id": resolved_guide_id, "avg_grade": avg_grade},
        )
    else:
        log_event(
            "placement_failed",
            user_id,
            {"guide_id": resolved_guide_id, "avg_grade": avg_grade},
        )

    return {
        "results": results,
        "average_grade": round(avg_grade, 2),
        "passed": passed,
        "threshold": threshold,
        "completion": completion,
    }


def _sync_catalog(
    store: CurriculumStore,
    *,
    user_id: str | None = None,
    scanner: CurriculumScanner | None = None,
    catalog_fingerprint: str | None = None,
) -> int:
    """Run scanner and sync results into store."""
    scanner = scanner or CurriculumScanner(_content_dirs(user_id))
    guides, chapters = scanner.scan()
    if guides:
        store.sync_catalog(guides, chapters)
    store.reconcile_guide_aliases(scanner.get_guide_aliases())
    store.set_catalog_meta(
        "catalog_fingerprint",
        catalog_fingerprint or scanner.get_catalog_fingerprint(),
    )
    return len(guides)
