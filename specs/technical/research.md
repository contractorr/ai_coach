---
id: research
category: tracked_module
status: experimental
implements:
- deep-research
code_paths:
- src/research
- src/web/routes/research.py
- web/src/app/(dashboard)/research/page.tsx
- tests/research
last_reviewed: '2026-03-30'
---

# Research

**Status:** Updated for the simplified product model

## Overview

Research orchestration powers deep dives, dossier refreshes, and durable report generation behind Radar and Research.

## Key Modules

- research runners and summarizers
- `src/web/routes/research.py`
- Research report surfaces and Radar dossier actions

## Interfaces

- research start and refresh endpoints
- report generation and retrieval paths
- dossier-linked research execution

## Simplified Product Notes

- Research is entered from concrete work such as a thread, escalation, or active dossier.
- Archived outputs belong in Research for later reuse.
