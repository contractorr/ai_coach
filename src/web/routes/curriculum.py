"""Curriculum / Learn routes — guides, chapters, progress, reviews, quizzes, placement."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from curriculum.content_schema import load_curriculum_document, resolve_chapter_content_path
from curriculum.models import (
    BloomLevel,
    ChapterStatus,
    ProgressUpdate,
    QuizSubmission,
    ReviewGradeRequest,
    ReviewItemType,
)
from curriculum.personalization import build_applied_assessments, score_guide_candidate
from curriculum.question_generator import QuestionGenerator
from curriculum.scanner import CurriculumScanner, build_tree_layout
from curriculum.store import CurriculumStore
from web.auth import get_current_user
from web.deps import get_config, get_profile_path, get_user_paths
from web.user_store import log_event

logger = structlog.get_logger()
router = APIRouter(prefix="/api/curriculum", tags=["curriculum"])


def _content_dirs() -> list[Path]:
    """Resolve built-in + extra content directories."""
    # Built-in content: content/curriculum/ relative to repo root
    # Repo root = 3 levels up from src/web/routes/
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    dirs = [repo_root / "content" / "curriculum"]

    config = get_config()
    if hasattr(config, "curriculum") and config.curriculum.extra_content_dirs:
        for d in config.curriculum.extra_content_dirs:
            dirs.append(Path(d).expanduser().resolve())
    return dirs


def _get_store(user_id: str) -> CurriculumStore:
    paths = get_user_paths(user_id)
    return CurriculumStore(Path(paths["data_dir"]) / "curriculum.db")


def _ensure_catalog_initialized(
    store: CurriculumStore,
    scanner: CurriculumScanner | None = None,
) -> CurriculumScanner:
    """Populate the curriculum catalog on first use for this user DB."""
    scanner = scanner or CurriculumScanner(_content_dirs())
    if not store.list_guides():
        _sync_catalog(store, scanner)
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


def _decorate_guide_payload(
    guide: dict,
    scanner: CurriculumScanner,
    program_lookup: dict[str, list[dict]] | None = None,
    *,
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
    }
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


def _recommendation_reason(stage: str, recommendation_meta: dict, fallback: str) -> str:
    matched_programs = recommendation_meta.get("matched_programs", [])
    if matched_programs and stage in {"ready", "entry"}:
        return f"Best fit right now for {matched_programs[0]['title']}."
    signals = recommendation_meta.get("signals", [])
    if stage in {"ready", "entry"}:
        for signal in signals:
            if signal.get("kind") in {"context", "industry", "time"}:
                return signal.get("detail", fallback)
    return fallback


def _build_next_payload(
    guide: dict,
    scanner: CurriculumScanner,
    program_lookup: dict[str, list[dict]],
    profile,
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


def _chapter_content_path(chapter_id: str) -> Path | None:
    """Resolve chapter markdown file from content dirs.

    chapter_id format: guide_id/chapter_stem
    """
    return resolve_chapter_content_path(_content_dirs(), chapter_id)


def _load_chapter_document(chapter_id: str, filename: str | None = None):
    content_path = resolve_chapter_content_path(_content_dirs(), chapter_id, filename=filename)
    if not content_path:
        return None, None
    return content_path, load_curriculum_document(content_path)


# --- Endpoints ---


@router.get("/tracks")
async def list_tracks(
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _ensure_catalog_initialized(store, CurriculumScanner(_content_dirs()))
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
    scanner = _ensure_catalog_initialized(store, CurriculumScanner(_content_dirs()))
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
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _ensure_catalog_initialized(store, CurriculumScanner(_content_dirs()))
    guide_aliases = set(scanner.get_guide_aliases())
    program_lookup = _build_program_lookup(scanner.get_learning_programs())

    guides = store.list_guides(category=category, user_id=user_id)
    visible_guides = [
        guide for guide in guides if guide["id"] not in guide_aliases or guide.get("enrolled")
    ]
    return [_decorate_guide_payload(guide, scanner, program_lookup) for guide in visible_guides]


@router.get("/guides/{guide_id}")
async def get_guide(
    guide_id: str,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    scanner = _ensure_catalog_initialized(store, CurriculumScanner(_content_dirs()))
    resolved_guide_id = _resolve_guide_id(scanner, guide_id)
    program_lookup = _build_program_lookup(scanner.get_learning_programs())
    profile = _load_user_profile(user["id"])
    guide = store.get_guide(resolved_guide_id, user_id=user["id"])
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    next_chapter = store.get_next_chapter(user["id"], resolved_guide_id)
    return _decorate_guide_payload(
        guide,
        scanner,
        program_lookup,
        profile=profile,
        include_applied_assessments=True,
        assessment_chapter_title=next_chapter["title"] if next_chapter else None,
    )


@router.get("/guides/{guide_id}/chapters/{chapter_id:path}")
async def get_chapter(
    guide_id: str,
    chapter_id: str,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    scanner = _ensure_catalog_initialized(store, CurriculumScanner(_content_dirs()))
    resolved_guide_id = _resolve_guide_id(scanner, guide_id)

    # chapter_id comes in as the part after guide_id, reconstruct full id
    full_chapter_id = f"{resolved_guide_id}/{chapter_id}"
    chapter = store.get_chapter(full_chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Read content
    _, document = _load_chapter_document(full_chapter_id, chapter.get("filename"))
    if not document:
        raise HTTPException(status_code=404, detail="Chapter content file not found")

    # Get progress
    progress = store.get_chapter_progress(user["id"], full_chapter_id)

    # Compute prev/next
    guide = store.get_guide(resolved_guide_id, user_id=user["id"])
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

    return {
        **chapter,
        "content": document.body,
        "progress": progress,
        "prev_chapter": prev_chapter,
        "next_chapter": next_chapter,
    }


@router.post("/guides/{guide_id}/enroll", status_code=status.HTTP_201_CREATED)
async def enroll_guide(
    guide_id: str,
    create_goal: bool = Query(True),
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _ensure_catalog_initialized(store, CurriculumScanner(_content_dirs()))
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
    result = store.update_progress(
        user_id=user_id,
        chapter_id=body.chapter_id,
        guide_id=body.guide_id,
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
            {"chapter_id": body.chapter_id, "guide_id": body.guide_id},
        )

        # Reflection prompt
        try:
            chapter = store.get_chapter(body.chapter_id)
            ch_title = chapter["title"] if chapter else body.chapter_id
            guide = store.get_guide(body.guide_id)
            g_title = guide["title"] if guide else body.guide_id
            guide_complete = _is_guide_just_completed(store, user_id, body.guide_id)
            reflection_prompt = _generate_reflection_prompt(ch_title, g_title, guide_complete)
        except Exception as exc:
            logger.debug("reflection_prompt_failed", error=str(exc))

        # Memory extraction from chapter content
        try:
            config = get_config()
            if config.memory.enabled:
                _, document = _load_chapter_document(body.chapter_id)
                if document:
                    text = document.body[:3000]
                    from memory.pipeline import MemoryPipeline
                    from web.deps import get_memory_store

                    fact_store = get_memory_store(user_id)
                    pipeline = MemoryPipeline(fact_store)
                    updates = pipeline.process_document(
                        document_id=f"curriculum:{body.chapter_id}",
                        document_text=text,
                        document_metadata={
                            "source_type": "curriculum",
                            "guide_id": body.guide_id,
                            "chapter_id": body.chapter_id,
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


@router.get("/review/due")
async def get_due_reviews(
    guide_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    return store.get_due_reviews(user["id"], limit=limit, guide_id=guide_id)


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
    else:
        # LLM grading
        try:
            gen = QuestionGenerator()
            bloom = BloomLevel(item["bloom_level"])
            result = await gen.grade_answer(
                question=item["question"],
                expected_answer=item["expected_answer"],
                student_answer=body.answer,
                bloom_level=bloom,
            )
            grade = result.grade
        except Exception:
            grade = 3  # default if grading fails

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
    return {"review": updated, "grade": grade}


@router.post("/quiz/{chapter_id:path}/generate")
async def generate_quiz(
    chapter_id: str,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    chapter = store.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Check if questions already exist
    existing = [
        item
        for item in store.get_review_items_for_chapter(user["id"], chapter_id)
        if item.get("item_type") == ReviewItemType.QUIZ.value
    ]
    if existing:
        return {"questions": existing, "cached": True}

    # Read content
    _, document = _load_chapter_document(chapter_id, chapter.get("filename"))
    if not document:
        raise HTTPException(status_code=404, detail="Chapter content not found")

    # Get guide title
    guide = store.get_guide(chapter["guide_id"])
    guide_title = guide["title"] if guide else ""

    gen = QuestionGenerator()
    items = await gen.generate_questions(
        content=document.body,
        chapter_title=chapter["title"],
        guide_title=guide_title,
        count=5,
        content_hash=chapter["content_hash"],
        chapter_id=chapter_id,
        guide_id=chapter["guide_id"],
        user_id=user["id"],
    )

    if items:
        store.add_review_items(items)

    quiz_items = [i.model_dump() for i in items if i.item_type == ReviewItemType.QUIZ]
    return {"questions": quiz_items, "cached": False}


@router.post("/quiz/{chapter_id:path}/submit")
async def submit_quiz(
    chapter_id: str,
    body: QuizSubmission,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    results = []

    for question_id, answer in body.answers.items():
        item = store.get_review_item(question_id)
        if not item:
            continue

        gen = QuestionGenerator()
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
            "chapter_id": chapter_id,
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
    chapter = store.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Must be completed
    progress = store.get_chapter_progress(user_id, chapter_id)
    if not progress or progress.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Chapter not completed")

    # Return cached
    existing = store.get_teachback_for_chapter(user_id, chapter_id)
    if existing:
        return {
            "concept": existing["question"].removeprefix("Explain ").split(" as if ")[0],
            "prompt": existing["question"],
            "review_item_id": existing["id"],
        }

    # Generate
    _, document = _load_chapter_document(chapter_id, chapter.get("filename"))
    if not document:
        raise HTTPException(status_code=404, detail="Chapter content not found")

    guide = store.get_guide(chapter["guide_id"])
    guide_title = guide["title"] if guide else ""

    gen = QuestionGenerator()
    item = await gen.generate_teachback(
        content=document.body,
        chapter_title=chapter["title"],
        guide_title=guide_title,
        content_hash=chapter["content_hash"],
        chapter_id=chapter_id,
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

    gen = QuestionGenerator()
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
    chapter = store.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Return cached
    existing = store.get_pre_reading_questions(user_id, chapter_id)
    if existing:
        return {"questions": existing}

    # Generate (includes both quiz + pre-reading items)
    _, document = _load_chapter_document(chapter_id, chapter.get("filename"))
    if not document:
        return {"questions": []}

    guide = store.get_guide(chapter["guide_id"])
    guide_title = guide["title"] if guide else ""

    gen = QuestionGenerator()
    items = await gen.generate_questions(
        content=document.body,
        chapter_title=chapter["title"],
        guide_title=guide_title,
        count=config.curriculum.questions_per_chapter,
        content_hash=chapter["content_hash"],
        chapter_id=chapter_id,
        guide_id=chapter["guide_id"],
        user_id=user_id,
        include_pre_reading=True,
        pre_reading_count=config.curriculum.pre_reading_count,
    )

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
    chapter = store.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Get enrolled guide IDs
    enrollments = store.get_enrollments(user_id)
    enrolled_ids = [e["guide_id"] for e in enrollments]
    if len(enrolled_ids) < 2:
        return {"related": []}

    # Read current chapter content
    _, document = _load_chapter_document(chapter_id, chapter.get("filename"))
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
            _, document = _load_chapter_document(ch_id, chapter.get("filename"))
            return document.body if document else None

        emb.sync_from_chapters(all_chapters, reader)

    return emb


@router.get("/stats")
async def get_stats(user: dict = Depends(get_current_user)):
    store = _get_store(user["id"])
    _ensure_catalog_initialized(store)
    stats = store.get_stats(user["id"])
    return stats.model_dump()


@router.post("/sync")
async def sync_content(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    store = _get_store(user_id)
    count = _sync_catalog(store)
    logger.info("curriculum.sync_completed", user_id=user_id, guide_count=count)
    return {"synced_guides": count, "message": f"Synced {count} guides with latest track data"}


@router.get("/ready")
async def get_ready_guides(
    user: dict = Depends(get_current_user),
):
    """Return guides whose prerequisites are all completed but not yet enrolled."""
    store = _get_store(user["id"])
    scanner = _ensure_catalog_initialized(store, CurriculumScanner(_content_dirs()))
    guide_aliases = set(scanner.get_guide_aliases())
    program_lookup = _build_program_lookup(scanner.get_learning_programs())
    ready_guides = store.get_ready_guides(user["id"], excluded_guide_ids=guide_aliases)
    return [_decorate_guide_payload(guide, scanner, program_lookup) for guide in ready_guides]


@router.get("/next")
async def get_next_recommendation(
    user: dict = Depends(get_current_user),
):
    """Get advisor-recommended next chapter/guide to study (DAG-aware)."""
    user_id = user["id"]
    store = _get_store(user_id)
    scanner = _ensure_catalog_initialized(store, CurriculumScanner(_content_dirs()))
    guide_aliases = set(scanner.get_guide_aliases())
    return _get_next_recommendation_v2(user_id, store, scanner, guide_aliases)


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
    scanner = CurriculumScanner(_content_dirs())
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

    gen = QuestionGenerator()
    all_questions: list[dict] = []
    max_q = config.curriculum.placement_max_questions
    per_ch = config.curriculum.placement_questions_per_chapter

    for ch in chapters:
        if len(all_questions) >= max_q:
            break
        _, document = _load_chapter_document(ch["id"], ch.get("filename"))
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
    scanner = CurriculumScanner(_content_dirs())
    resolved_guide_id = _resolve_guide_id(scanner, guide_id)

    cache_key = (user_id, resolved_guide_id)
    cached = _placement_cache.get(cache_key)
    if not cached:
        raise HTTPException(status_code=410, detail="Placement session expired or not found")

    if datetime.utcnow() - cached["created_at"] > _PLACEMENT_TTL:
        _placement_cache.pop(cache_key, None)
        raise HTTPException(status_code=410, detail="Placement session expired")

    questions_by_id = {q["id"]: q for q in cached["questions"]}
    gen = QuestionGenerator()
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


def _sync_catalog(store: CurriculumStore, scanner: CurriculumScanner | None = None) -> int:
    """Run scanner and sync results into store."""
    scanner = scanner or CurriculumScanner(_content_dirs())
    guides, chapters = scanner.scan()
    if guides:
        store.sync_catalog(guides, chapters)
    store.reconcile_guide_aliases(scanner.get_guide_aliases())
    return len(guides)
