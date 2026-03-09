"""Observability: metrics collection and run summary logging."""

import threading
import time
from contextlib import contextmanager
from typing import Any

import structlog

logger = structlog.get_logger().bind(source="observability")


class Metrics:
    """Simple dict-based metrics collector for counters and timers."""

    _PRICING_PER_MILLION = (
        ("gpt-4o-mini", 0.15, 0.60),
        ("gpt-4o", 2.50, 10.00),
        ("haiku", 0.25, 1.25),
        ("sonnet", 3.00, 15.00),
        ("opus", 15.00, 75.00),
        ("gemini", 0.00, 0.00),
    )

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: dict[str, int] = {}
        self._timers: dict[str, list[float]] = {}
        self._tokens: dict[str, dict[str, float]] = {}

    def counter(self, name: str, value: int = 1):
        """Increment a counter by the given value."""
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value

    @contextmanager
    def timer(self, name: str):
        """Context manager to time an operation and store duration."""
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            with self._lock:
                if name not in self._timers:
                    self._timers[name] = []
                self._timers[name].append(duration)

    def token_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        *,
        cache_creation_input_tokens: int = 0,
        cache_read_input_tokens: int = 0,
        billed_input_tokens: float | None = None,
    ) -> None:
        """Track per-model token usage and billed-token adjustments."""
        normalized_model = (model or "unknown").strip() or "unknown"
        effective_billed_input = (
            float(billed_input_tokens)
            if billed_input_tokens is not None
            else float(input_tokens + cache_creation_input_tokens)
        )
        with self._lock:
            entry = self._tokens.setdefault(
                normalized_model,
                {
                    "input_tokens": 0.0,
                    "output_tokens": 0.0,
                    "cache_creation_input_tokens": 0.0,
                    "cache_read_input_tokens": 0.0,
                    "billed_input_tokens": 0.0,
                },
            )
            entry["input_tokens"] += input_tokens
            entry["output_tokens"] += output_tokens
            entry["cache_creation_input_tokens"] += cache_creation_input_tokens
            entry["cache_read_input_tokens"] += cache_read_input_tokens
            entry["billed_input_tokens"] += effective_billed_input

    def _get_pricing(self, model: str) -> tuple[float, float, bool]:
        lower_model = model.lower()
        for pattern, input_rate, output_rate in self._PRICING_PER_MILLION:
            if pattern in lower_model:
                return input_rate, output_rate, True
        return 0.0, 0.0, False

    def summary(self) -> dict[str, Any]:
        """Return a summary of all collected metrics."""
        with self._lock:
            counters = dict(self._counters)
            timers = {name: list(durations) for name, durations in self._timers.items()}
            tokens = {name: dict(values) for name, values in self._tokens.items()}

        timer_summary = {}
        for name, durations in timers.items():
            if durations:
                timer_summary[name] = {
                    "count": len(durations),
                    "total": sum(durations),
                    "avg": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                }
            else:
                timer_summary[name] = {"count": 0}

        token_summary = {}
        for model, usage in tokens.items():
            input_rate, output_rate, has_pricing = self._get_pricing(model)
            estimated_cost = (usage["billed_input_tokens"] / 1_000_000.0) * input_rate + (
                usage["output_tokens"] / 1_000_000.0
            ) * output_rate
            token_summary[model] = {
                "input_tokens": int(usage["input_tokens"]),
                "output_tokens": int(usage["output_tokens"]),
                "cache_creation_input_tokens": int(usage["cache_creation_input_tokens"]),
                "cache_read_input_tokens": int(usage["cache_read_input_tokens"]),
                "billed_input_tokens": round(usage["billed_input_tokens"], 2),
                "estimated_cost_usd": round(estimated_cost, 6),
                "has_pricing": has_pricing,
            }

        return {
            "counters": counters,
            "timers": timer_summary,
            "token_usage": token_summary,
        }

    def reset(self):
        """Clear all metrics."""
        with self._lock:
            self._counters.clear()
            self._timers.clear()
            self._tokens.clear()


# Module-level singleton
metrics = Metrics()


def log_run_summary():
    """Log the current metrics summary via structlog."""
    summary = metrics.summary()
    logger.info("run_summary", **summary)
