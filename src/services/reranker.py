"""Optional cross-encoder reranker — requires sentence-transformers."""

from __future__ import annotations

import structlog

logger = structlog.get_logger()


class CrossEncoderReranker:
    """Rerank passages using a cross-encoder model.

    Requires `pip install stewardme[reranking]`. When sentence-transformers
    is not installed, `self.available` is False and `rerank()` returns
    identity ordering.
    """

    MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self) -> None:
        self.available = False
        self._model = None
        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.MODEL)
            self.available = True
        except ImportError:
            logger.debug("cross_encoder_unavailable", reason="sentence-transformers not installed")
        except Exception as exc:
            logger.warning("cross_encoder_init_failed", error=str(exc))

    def rerank(self, query: str, passages: list[str], top_k: int = 10) -> list[int]:
        """Return indices of passages sorted by relevance to query.

        When cross-encoder is unavailable, returns original ordering.
        """
        if not passages:
            return []
        if not self.available or not self._model:
            return list(range(min(top_k, len(passages))))

        try:
            pairs = [[query, p] for p in passages]
            scores = self._model.predict(pairs)
            ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            return ranked[:top_k]
        except Exception as exc:
            logger.warning("cross_encoder_rerank_failed", error=str(exc))
            return list(range(min(top_k, len(passages))))
