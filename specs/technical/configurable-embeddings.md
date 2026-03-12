# Configurable Embeddings

## Overview

Pluggable embedding provider system mirroring `src/llm/factory.py` auto-detection. Ships Gemini and OpenAI providers plus the existing hash fallback. A single factory function (`create_embedding_function`) returns a callable matching the `__call__(Iterable[str]) -> list[list[float]]` contract used by `LocalCollection`.

## Dependencies

**Depends on:** `google-generativeai` (existing), `openai` (existing)
**Depended on by:** `chroma_utils.LocalCollection`, `journal.embeddings`, `intelligence.embeddings`, `memory.store`

---

## Components

### EmbeddingFunction (ABC)
**File:** `src/embeddings/base.py`
**Status:** Stable

#### Behavior
Abstract base. Subclasses implement `__call__` and declare `provider_name` + `dimensions`.

#### Inputs / Outputs
```python
class EmbeddingFunction(ABC):
    provider_name: str
    dimensions: int
    def __call__(self, input: Iterable[str]) -> list[list[float]]: ...
    def name(self) -> str: ...
```

---

### GeminiEmbeddingFunction
**File:** `src/embeddings/gemini.py`
**Status:** Stable

#### Behavior
- Model: `gemini-embedding-2-preview` (configurable)
- Default dimensions: 768
- Batches inputs in chunks of 100 (API limit)
- Uses `google.generativeai.embed_content()`

#### Configuration
| Key | Default | Source |
|-----|---------|--------|
| `embeddings.model` | `gemini-embedding-2-preview` | config.yaml |
| `embeddings.dimensions` | 768 | config.yaml |
| `GOOGLE_API_KEY` | — | env var |

---

### OpenAIEmbeddingFunction
**File:** `src/embeddings/openai.py`
**Status:** Stable

#### Behavior
- Model: `text-embedding-3-small` (configurable)
- Default dimensions: 1536
- Uses `openai.OpenAI().embeddings.create()`

#### Configuration
| Key | Default | Source |
|-----|---------|--------|
| `embeddings.model` | `text-embedding-3-small` | config.yaml |
| `embeddings.dimensions` | 1536 | config.yaml |
| `OPENAI_API_KEY` | — | env var |

---

### create_embedding_function (factory)
**File:** `src/embeddings/factory.py`
**Status:** Stable

#### Behavior
```
Detection order: gemini → openai → hash fallback
1. If provider == "hash" → SimpleHashEmbeddingFunction
2. If provider == "gemini" or "openai" → instantiate directly
3. If provider == "auto" or None:
   a. GOOGLE_API_KEY present → GeminiEmbeddingFunction
   b. OPENAI_API_KEY present → OpenAIEmbeddingFunction
   c. else → SimpleHashEmbeddingFunction (from chroma_utils)
```

#### Inputs / Outputs
```python
def create_embedding_function(
    provider: str | None = None,  # auto/gemini/openai/hash
    model: str | None = None,
    dimensions: int | None = None,
    config: dict | None = None,   # reads embeddings.* keys
) -> EmbeddingFunction | SimpleHashEmbeddingFunction
```

Reads `config["embeddings"]` if provided, CLI args override config values.

---

### Integration: chroma_utils.py
**File:** `src/chroma_utils.py`

`build_embedding_function()` delegates to `create_embedding_function()`. `SimpleHashEmbeddingFunction` stays in this file as the zero-dependency fallback. `COACH_USE_ONNX_EMBEDDINGS` env var check removed.

### Integration: memory/store.py
**File:** `src/memory/store.py`

`FactStore._chroma` property passes `embedding_function=create_embedding_function()` to `client.get_or_create_collection()`. Removes dependency on ChromaDB's built-in ONNX embeddings.

---

## Test Expectations

- Factory returns hash fallback when no API keys set
- Factory returns Gemini when `GOOGLE_API_KEY` set
- Factory returns OpenAI when `OPENAI_API_KEY` set (no Google key)
- Explicit `provider="hash"` always returns hash regardless of env
- Config dict values respected when passed
- Hash fallback produces deterministic, normalized vectors
- All existing tests pass (they run without API keys → hash fallback)
