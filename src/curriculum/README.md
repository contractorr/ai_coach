# Curriculum Package

Structured learning content, progress tracking, reviews, and generated practice live here.

## Entry Points

- `store.py`: canonical curriculum persistence and derived reads
- `scanner.py`: content ingestion and indexing
- `question_generator.py`: generated quizzes and assessments
- `models.py`: curriculum domain models

## Invariants

- Built-in content stays repository-backed; user-authored guide flows must preserve origin metadata.
- Contract changes usually touch both `src/web/routes/curriculum.py` and `web/src/types/curriculum.ts`.
- `store.py` is a hotspot; prefer narrow helper extraction over in-place expansion.

## Validation

- `just test-curriculum`
- `uv run pytest tests/curriculum/test_store.py tests/curriculum/test_scanner.py -q`
- `uv run pytest tests/web/test_curriculum_routes.py -q`
