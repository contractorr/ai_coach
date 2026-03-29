# Advisor Package

Core conversational and recommendation orchestration lives here.

## Entry Points

- `engine.py`: main ask/reply workflow
- `agentic.py`: tool-using advisor mode
- `recommendations.py`: recommendation assembly and scoring
- `context_assembler.py`: merges journal, intel, profile, and memory context

## Invariants

- Surface layers call advisor services through `web/routes/advisor.py`, CLI commands, or MCP tools.
- Prompt changes should update the relevant functional and technical specs first.
- Recommendation behavior changes usually affect both ranking logic and user-facing payloads.

## Validation

- `just test-advisor`
- `uv run pytest tests/advisor/test_engine.py tests/advisor/test_agentic.py -q`
- `uv run pytest tests/web/test_advisor_routes.py -q`
